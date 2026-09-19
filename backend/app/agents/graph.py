import structlog
from langgraph.graph import StateGraph, END
from app.agents.state import RunGraphState
from app.agents.intake_agent import intake_node
from app.agents.planning_agent import planning_node
from app.agents.review_agent import review_node
from app.config import get_settings

logger = structlog.get_logger()


def should_continue_review(state: RunGraphState) -> str:
    """
    Decide whether to loop back to planning or end.

    Ends the loop if:
    1. Review approved the plan
    2. Max review cycles reached (hard cap)
    3. Convergence stalled (corrections aren't decreasing — soft cap)
    4. An error occurred (simulated failure)
    5. Only minor corrections remain on elevated/final urgency
    """
    settings = get_settings()

    # Error -> end
    if state.get("error"):
        return "end"

    review_output = state.get("review_output")
    if not review_output:
        return "end"

    # Approved -> end
    if review_output.get("approved", False):
        logger.info("review_approved", run_id=state["run_id"])
        return "end"

    attempt = state.get("review_attempt", 0)

    # Hard cap -> end with unresolved issues
    if attempt >= settings.max_review_cycles:
        logger.warning(
            "review_hard_cap_reached",
            run_id=state["run_id"],
            attempts=attempt,
            max=settings.max_review_cycles,
        )
        return "end"

    # Convergence stalled -> end early (loop is stuck)
    if state.get("convergence_stalled", False):
        logger.warning(
            "review_convergence_stalled",
            run_id=state["run_id"],
            attempts=attempt,
            message="Loop not converging — stopping early to avoid wasted tokens",
        )
        return "end"

    # Only minor issues left on second-to-last or last attempt -> end
    corrections = review_output.get("corrections", [])
    if attempt >= settings.max_review_cycles - 1:
        severities = [c.get("severity", "major") for c in corrections]
        if all(s == "minor" for s in severities):
            logger.info(
                "review_minor_only_late_stage",
                run_id=state["run_id"],
                attempt=attempt,
                message="Only minor issues remain on late attempt — accepting plan",
            )
            return "end"

    # Loop back to planning with corrections
    logger.info(
        "review_loop_back",
        run_id=state["run_id"],
        attempt=attempt,
        corrections=len(corrections),
        history_size=len(state.get("correction_history", [])),
    )
    return "planning"


def should_continue_after_intake(state: RunGraphState) -> str:
    if state.get("error"):
        return "end"
    return "planning"


def should_continue_after_planning(state: RunGraphState) -> str:
    if state.get("error"):
        return "end"
    return "review"


def build_graph() -> StateGraph:
    """Build the LangGraph state graph for the 3-agent pipeline."""
    graph = StateGraph(RunGraphState)

    graph.add_node("intake", intake_node)
    graph.add_node("planning", planning_node)
    graph.add_node("review", review_node)

    graph.set_entry_point("intake")

    graph.add_conditional_edges(
        "intake",
        should_continue_after_intake,
        {"planning": "planning", "end": END},
    )

    graph.add_conditional_edges(
        "planning",
        should_continue_after_planning,
        {"review": "review", "end": END},
    )

    graph.add_conditional_edges(
        "review",
        should_continue_review,
        {"planning": "planning", "end": END},
    )

    return graph


def compile_graph():
    graph = build_graph()
    return graph.compile()
