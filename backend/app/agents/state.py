from typing import TypedDict


class CorrectionRecord(TypedDict, total=False):
    """A single correction with its resolution status across iterations."""
    issue: str
    evidence: str
    required_change: str
    related_task_ids: list[str]
    raised_at_attempt: int
    resolved_at_attempt: int | None
    status: str  # "open", "resolved", "regressed", "persistent"


class LoopIteration(TypedDict, total=False):
    """Telemetry for one review-planning loop iteration."""
    attempt: int
    corrections_raised: int
    corrections_resolved: int
    corrections_new: int
    corrections_regressed: int
    planning_tokens_in: int
    planning_tokens_out: int
    review_tokens_in: int
    review_tokens_out: int
    planning_changes_summary: str


class RunGraphState(TypedDict, total=False):
    run_id: str
    transcript: str
    rules: str
    intake_output: dict | None
    planning_output: dict | None
    review_output: dict | None
    review_attempt: int
    corrections: list[dict]
    simulated_failure_at: str | None
    error: str | None
    status: str

    # Loop engineering state
    correction_history: list[dict]      # Full history of all corrections across iterations
    loop_iterations: list[dict]         # Per-iteration telemetry
    previous_plans: list[dict]          # All previous planning outputs for diff tracking
    planning_change_log: list[str]      # What planning changed in each iteration
    convergence_stalled: bool           # True if corrections aren't decreasing
