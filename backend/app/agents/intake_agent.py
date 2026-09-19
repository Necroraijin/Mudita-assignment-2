import json
import structlog
from app.agents.llm import call_llm, parse_json_response
from app.agents.prompts import INTAKE_SYSTEM_PROMPT, INTAKE_USER_PROMPT
from app.agents.state import RunGraphState
from app.schemas.intake import IntakeOutput

logger = structlog.get_logger()


class SimulatedFailureError(Exception):
    pass


def intake_node(state: RunGraphState) -> dict:
    run_id = state["run_id"]

    # Check for simulated failure
    if state.get("simulated_failure_at") == "intake":
        logger.warning("simulated_failure", run_id=run_id, agent="intake")
        return {
            "simulated_failure_at": None,
            "error": "[simulated fault] Model call failed at intake agent",
            "status": "failed",
        }

    user_prompt = INTAKE_USER_PROMPT.format(
        transcript=state["transcript"],
        rules=state["rules"],
    )

    response = call_llm(
        system_prompt=INTAKE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        run_id=run_id,
        agent_name="intake",
    )

    parsed = parse_json_response(response.content)

    # Validate against schema
    intake_output = IntakeOutput(**parsed)

    logger.info(
        "intake_completed",
        run_id=run_id,
        facts_count=len(intake_output.facts),
        gaps_count=len(intake_output.gaps),
        conflicts_count=len(intake_output.conflicts),
    )

    return {
        "intake_output": intake_output.model_dump(),
        "status": "running",
    }
