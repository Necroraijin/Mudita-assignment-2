import json
import structlog
from app.agents.llm import call_llm, parse_json_response
from app.agents.prompts import (
    PLANNING_SYSTEM_PROMPT,
    PLANNING_USER_PROMPT,
    PLANNING_CORRECTIONS_SECTION,
    PLANNING_CORRECTIONS_WITH_HISTORY,
    PLANNING_URGENCY_NORMAL,
    PLANNING_URGENCY_ELEVATED,
    PLANNING_URGENCY_FINAL,
)
from app.agents.state import RunGraphState
from app.agents.loop_engine import compute_plan_diff, build_progressive_context
from app.schemas.planning import PlanningOutput
from app.config import get_settings

logger = structlog.get_logger()

URGENCY_MESSAGES = {
    "normal": PLANNING_URGENCY_NORMAL,
    "elevated": PLANNING_URGENCY_ELEVATED,
    "final": PLANNING_URGENCY_FINAL,
}


def planning_node(state: RunGraphState) -> dict:
    run_id = state["run_id"]
    settings = get_settings()

    # Check for simulated failure
    if state.get("simulated_failure_at") == "planning":
        logger.warning("simulated_failure", run_id=run_id, agent="planning")
        return {
            "simulated_failure_at": None,
            "error": "[simulated fault] Model call failed at planning agent",
            "status": "failed",
        }

    intake_output = state["intake_output"]
    corrections = state.get("corrections", [])
    correction_history = state.get("correction_history", [])
    loop_iterations = state.get("loop_iterations", [])
    previous_plans = state.get("previous_plans", [])
    attempt = state.get("review_attempt", 0)

    # Build corrections section based on loop state
    corrections_section = ""
    if corrections:
        if correction_history:
            # We have loop history — use the enhanced template
            context = build_progressive_context(
                correction_history=correction_history,
                loop_iterations=loop_iterations,
                previous_plans=previous_plans,
                attempt=attempt + 1,
                max_attempts=settings.max_review_cycles,
            )

            # Format correction history summary
            history_lines = []
            for h in correction_history:
                status_tag = h["status"].upper()
                line = f"[{status_tag}] {h['issue']} (raised attempt {h.get('raised_at_attempt', '?')}"
                if h.get("resolved_at_attempt"):
                    line += f", resolved attempt {h['resolved_at_attempt']}"
                line += ")"
                history_lines.append(line)

            # Format previous changes
            prev_changes = []
            for i, plan in enumerate(previous_plans):
                change_log = plan.get("change_log", [])
                if change_log:
                    prev_changes.append(f"Iteration {i + 1}: " + "; ".join(change_log))

            corrections_section = PLANNING_CORRECTIONS_WITH_HISTORY.format(
                attempt=attempt + 1,
                max_attempts=settings.max_review_cycles,
                urgency=context["urgency_level"].upper(),
                urgency_message=URGENCY_MESSAGES.get(context["urgency_level"], ""),
                current_corrections=json.dumps(corrections, indent=2),
                correction_history_summary="\n".join(history_lines) if history_lines else "No history yet.",
                previous_changes="\n".join(prev_changes) if prev_changes else "No previous changes.",
            )
        else:
            # First loop back — use simple template
            corrections_section = PLANNING_CORRECTIONS_SECTION.format(
                corrections=json.dumps(corrections, indent=2)
            )

    user_prompt = PLANNING_USER_PROMPT.format(
        facts=json.dumps(intake_output.get("facts", []), indent=2),
        rules=state["rules"],
        gaps=json.dumps(intake_output.get("gaps", []), indent=2),
        conflicts=json.dumps(intake_output.get("conflicts", []), indent=2),
        corrections_section=corrections_section,
    )

    response = call_llm(
        system_prompt=PLANNING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        run_id=run_id,
        agent_name="planning",
        step=f"attempt_{attempt + 1}",
    )

    parsed = parse_json_response(response.content)
    planning_output = PlanningOutput(**parsed)

    # Compute plan diff for tracking
    prev_plan = previous_plans[-1] if previous_plans else None
    plan_diff = compute_plan_diff(prev_plan, planning_output.model_dump())

    # Update previous plans list
    updated_previous_plans = list(previous_plans) + [planning_output.model_dump()]

    # Track change log
    planning_change_log = list(state.get("planning_change_log", []))
    planning_change_log.append(
        f"Attempt {attempt + 1}: {plan_diff}"
    )

    logger.info(
        "planning_completed",
        run_id=run_id,
        tasks_count=len(planning_output.tasks),
        has_corrections=len(corrections) > 0,
        changes=len(planning_output.change_log),
        plan_diff_preview=plan_diff[:200],
    )

    return {
        "planning_output": planning_output.model_dump(),
        "previous_plans": updated_previous_plans,
        "planning_change_log": planning_change_log,
        "planning_tokens": {"in": response.tokens_in, "out": response.tokens_out},
        "status": "running",
    }
