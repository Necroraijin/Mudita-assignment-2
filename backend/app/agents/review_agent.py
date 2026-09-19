import json
import structlog
from app.agents.llm import call_llm, parse_json_response
from app.agents.prompts import (
    REVIEW_SYSTEM_PROMPT,
    REVIEW_USER_PROMPT,
    REVIEW_FIRST_ATTEMPT,
    REVIEW_SUBSEQUENT_ATTEMPT,
)
from app.agents.state import RunGraphState
from app.agents.loop_engine import (
    build_correction_history,
    build_loop_iteration,
    detect_convergence,
)
from app.schemas.review import ReviewOutput
from app.config import get_settings

logger = structlog.get_logger()


def review_node(state: RunGraphState) -> dict:
    run_id = state["run_id"]
    settings = get_settings()
    attempt = state.get("review_attempt", 0) + 1

    # Check for simulated failure
    if state.get("simulated_failure_at") == "review":
        logger.warning("simulated_failure", run_id=run_id, agent="review")
        return {
            "simulated_failure_at": None,
            "error": "[simulated fault] Model call failed at review agent",
            "status": "failed",
        }

    correction_history = state.get("correction_history", [])
    loop_iterations = state.get("loop_iterations", [])

    # Build loop-aware context for the prompt
    if attempt == 1:
        loop_context = REVIEW_FIRST_ATTEMPT.format(
            max_attempts=settings.max_review_cycles,
        )
    else:
        # Format resolved issues
        resolved = [h for h in correction_history if h["status"] == "resolved"]
        resolved_text = "\n".join(
            f"- {h['issue']} (fixed at attempt {h.get('resolved_at_attempt', '?')})"
            for h in resolved
        ) if resolved else "None yet."

        # Format open issues
        open_issues = [h for h in correction_history if h["status"] == "open"]
        open_text = "\n".join(
            f"- {h['issue']} (raised at attempt {h.get('raised_at_attempt', '?')})"
            for h in open_issues
        ) if open_issues else "None."

        # Format persistent issues
        persistent = [h for h in correction_history if h["status"] == "persistent"]
        persistent_text = "\n".join(
            f"- {h['issue']} (raised at attempt {h.get('raised_at_attempt', '?')}, still unfixed)"
            for h in persistent
        ) if persistent else "None."

        # Format regressed issues
        regressed = [h for h in correction_history if h["status"] == "regressed"]
        regressed_text = "\n".join(
            f"- {h['issue']} (was fixed, now broken again)"
            for h in regressed
        ) if regressed else "None."

        # Get change log from planning
        change_log = state.get("planning_output", {}).get("change_log", [])
        change_log_text = "\n".join(f"- {c}" for c in change_log) if change_log else "No changes documented."

        # Format iteration summaries
        summaries = []
        for it in loop_iterations:
            summaries.append(
                f"Attempt {it['attempt']}: "
                f"{it['corrections_raised']} issues raised, "
                f"{it['corrections_resolved']} resolved, "
                f"{it['corrections_new']} new, "
                f"{it['corrections_regressed']} regressed"
            )
        summaries_text = "\n".join(summaries) if summaries else "No previous iterations."

        loop_context = REVIEW_SUBSEQUENT_ATTEMPT.format(
            attempt=attempt,
            max_attempts=settings.max_review_cycles,
            resolved_issues=resolved_text,
            open_issues=open_text,
            persistent_count=2,
            persistent_issues=persistent_text,
            regressed_issues=regressed_text,
            change_log=change_log_text,
            iteration_summaries=summaries_text,
        )

    user_prompt = REVIEW_USER_PROMPT.format(
        transcript=state["transcript"],
        rules=state["rules"],
        facts=json.dumps(state["intake_output"].get("facts", []), indent=2),
        plan=json.dumps(state["planning_output"], indent=2),
        loop_context=loop_context,
    )

    response = call_llm(
        system_prompt=REVIEW_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        run_id=run_id,
        agent_name="review",
        step=f"attempt_{attempt}",
    )

    parsed = parse_json_response(response.content)
    review_output = ReviewOutput(**parsed)

    # Update correction history with this iteration's results
    current_corrections = [c.model_dump() for c in review_output.corrections]
    updated_history = build_correction_history(
        current_corrections=current_corrections,
        previous_history=correction_history,
        attempt=attempt,
    )

    # Build loop iteration telemetry
    planning_tokens = state.get("planning_tokens", {"in": 0, "out": 0})
    iteration = build_loop_iteration(
        attempt=attempt,
        current_corrections=current_corrections,
        correction_history=updated_history,
        planning_tokens=(planning_tokens.get("in", 0), planning_tokens.get("out", 0)),
        review_tokens=(response.tokens_in, response.tokens_out),
        changes_summary=state.get("planning_change_log", [""])[-1] if state.get("planning_change_log") else "",
    )
    updated_iterations = list(loop_iterations) + [iteration]

    # Check convergence
    stalled = detect_convergence(updated_iterations)

    if stalled:
        logger.warning(
            "loop_convergence_stalled",
            run_id=run_id,
            attempt=attempt,
            open_corrections=len(current_corrections),
        )

    logger.info(
        "review_completed",
        run_id=run_id,
        attempt=attempt,
        approved=review_output.approved,
        corrections_count=len(review_output.corrections),
        resolved_count=len(review_output.resolved_from_previous),
        history_open=len([h for h in updated_history if h["status"] in ("open", "persistent", "regressed")]),
        history_resolved=len([h for h in updated_history if h["status"] == "resolved"]),
        convergence_stalled=stalled,
    )

    return {
        "review_output": review_output.model_dump(),
        "review_attempt": attempt,
        "corrections": current_corrections,
        "correction_history": updated_history,
        "loop_iterations": updated_iterations,
        "convergence_stalled": stalled,
        "status": "running",
    }
