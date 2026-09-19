"""
Loop Engineering Module

Manages the Review <-> Planning feedback loop with:
- Correction history tracking (raised, resolved, regressed, persistent)
- Convergence detection (stop early if loop is stuck)
- Progressive context building (each iteration gets richer context)
- Diff tracking (what changed between plan versions)
- Per-iteration telemetry
"""

import structlog
from app.config import get_settings

logger = structlog.get_logger()


def build_correction_history(
    current_corrections: list[dict],
    previous_history: list[dict],
    attempt: int,
) -> list[dict]:
    """
    Merge new corrections into the running history.

    Each correction in history tracks:
    - When it was first raised
    - When/if it was resolved
    - If it regressed (was fixed then re-appeared)
    - If it's persistent (never fixed across multiple attempts)
    """
    # Index previous corrections by issue text for matching
    history_by_issue = {}
    for h in previous_history:
        history_by_issue[h["issue"]] = h

    updated_history = []

    # Check which previous corrections are resolved or still open
    current_issues = {c["issue"] for c in current_corrections}

    for prev in previous_history:
        issue = prev["issue"]
        if issue not in current_issues:
            # Was open, now gone -> resolved
            if prev["status"] in ("open", "regressed", "persistent"):
                resolved = {**prev, "resolved_at_attempt": attempt, "status": "resolved"}
                updated_history.append(resolved)
            else:
                updated_history.append(prev)
        # If still in current, we'll handle it below

    # Process current corrections
    for corr in current_corrections:
        issue = corr["issue"]
        if issue in history_by_issue:
            prev = history_by_issue[issue]
            if prev["status"] == "resolved":
                # Was fixed, now back -> regressed
                regressed = {
                    **prev,
                    "resolved_at_attempt": None,
                    "status": "regressed",
                }
                # Update in history (replace the resolved entry)
                updated_history = [
                    h if h["issue"] != issue else regressed
                    for h in updated_history
                ]
                if not any(h["issue"] == issue for h in updated_history):
                    updated_history.append(regressed)
            elif prev["status"] in ("open", "persistent"):
                # Still unfixed -> mark persistent if 2+ attempts
                age = attempt - prev.get("raised_at_attempt", 1)
                status = "persistent" if age >= 2 else "open"
                persistent = {**prev, "status": status}
                updated_history = [
                    h if h["issue"] != issue else persistent
                    for h in updated_history
                ]
                if not any(h["issue"] == issue for h in updated_history):
                    updated_history.append(persistent)
            elif prev["status"] == "regressed":
                # Already regressed, still not fixed
                if not any(h["issue"] == issue for h in updated_history):
                    updated_history.append(prev)
        else:
            # New correction
            new_entry = {
                "issue": corr["issue"],
                "evidence": corr.get("evidence", ""),
                "required_change": corr.get("required_change", ""),
                "related_task_ids": corr.get("related_task_ids", []),
                "raised_at_attempt": attempt,
                "resolved_at_attempt": None,
                "status": "open",
            }
            updated_history.append(new_entry)

    return updated_history


def detect_convergence(loop_iterations: list[dict]) -> bool:
    """
    Detect if the loop is stalled (not converging).

    Stalled = corrections aren't decreasing over the last 2 iterations.
    This catches infinite loops where Review keeps finding the same
    issues and Planning keeps not fixing them.
    """
    if len(loop_iterations) < 2:
        return False

    recent = loop_iterations[-2:]
    counts = [it.get("corrections_raised", 0) for it in recent]

    # Stalled if corrections haven't decreased at all
    if counts[-1] >= counts[-2]:
        # Also check if new corrections keep appearing
        new_counts = [it.get("corrections_new", 0) for it in recent]
        regressed_counts = [it.get("corrections_regressed", 0) for it in recent]

        # Definitely stalled if no new issues but count isn't dropping
        if new_counts[-1] == 0 and counts[-1] >= counts[-2]:
            return True

        # Stalled if regressions are happening
        if regressed_counts[-1] > 0:
            return True

    return False


def build_loop_iteration(
    attempt: int,
    current_corrections: list[dict],
    correction_history: list[dict],
    planning_tokens: tuple[int, int] = (0, 0),
    review_tokens: tuple[int, int] = (0, 0),
    changes_summary: str = "",
) -> dict:
    """Build telemetry for one loop iteration."""
    open_corrections = [h for h in correction_history if h["status"] == "open"]
    resolved_corrections = [
        h for h in correction_history
        if h["status"] == "resolved" and h.get("resolved_at_attempt") == attempt
    ]
    new_corrections = [
        h for h in correction_history
        if h.get("raised_at_attempt") == attempt and h["status"] == "open"
    ]
    regressed_corrections = [h for h in correction_history if h["status"] == "regressed"]

    return {
        "attempt": attempt,
        "corrections_raised": len(current_corrections),
        "corrections_resolved": len(resolved_corrections),
        "corrections_new": len(new_corrections),
        "corrections_regressed": len(regressed_corrections),
        "planning_tokens_in": planning_tokens[0],
        "planning_tokens_out": planning_tokens[1],
        "review_tokens_in": review_tokens[0],
        "review_tokens_out": review_tokens[1],
        "planning_changes_summary": changes_summary,
    }


def compute_plan_diff(previous_plan: dict | None, current_plan: dict) -> str:
    """
    Compute a human-readable diff between two planning outputs.
    Tracks added, removed, and modified tasks.
    """
    if not previous_plan:
        return "Initial plan created."

    prev_tasks = {t["task_id"]: t for t in previous_plan.get("tasks", [])}
    curr_tasks = {t["task_id"]: t for t in current_plan.get("tasks", [])}

    added = set(curr_tasks.keys()) - set(prev_tasks.keys())
    removed = set(prev_tasks.keys()) - set(curr_tasks.keys())
    common = set(prev_tasks.keys()) & set(curr_tasks.keys())

    changes = []

    if added:
        for tid in sorted(added):
            changes.append(f"ADDED {tid}: {curr_tasks[tid].get('description', '')[:80]}")

    if removed:
        for tid in sorted(removed):
            changes.append(f"REMOVED {tid}: {prev_tasks[tid].get('description', '')[:80]}")

    for tid in sorted(common):
        prev = prev_tasks[tid]
        curr = curr_tasks[tid]
        diffs = []
        for field in ("description", "owner", "deadline", "item_type", "priority"):
            if prev.get(field) != curr.get(field):
                diffs.append(f"{field}: '{prev.get(field)}' -> '{curr.get(field)}'")
        if set(prev.get("dependencies", [])) != set(curr.get("dependencies", [])):
            diffs.append(f"dependencies changed")
        if set(prev.get("source_fact_ids", [])) != set(curr.get("source_fact_ids", [])):
            diffs.append(f"source_fact_ids changed")
        if diffs:
            changes.append(f"MODIFIED {tid}: {', '.join(diffs)}")

    if not changes:
        return "No changes detected between plan versions."

    return "\n".join(changes)


def build_progressive_context(
    correction_history: list[dict],
    loop_iterations: list[dict],
    previous_plans: list[dict],
    attempt: int,
    max_attempts: int,
) -> dict:
    """
    Build context that gets richer and more urgent with each iteration.

    Returns a dict with:
    - correction_summary: formatted history of all corrections
    - urgency_level: "normal", "elevated", "final"
    - resolved_summary: what was successfully fixed
    - persistent_issues: issues that haven't been fixed
    - regressed_issues: issues that were fixed then broke again
    - iteration_summary: what happened in previous iterations
    """
    urgency = "normal"
    if attempt == max_attempts - 1:
        urgency = "elevated"
    elif attempt >= max_attempts:
        urgency = "final"

    open_issues = [h for h in correction_history if h["status"] == "open"]
    resolved_issues = [h for h in correction_history if h["status"] == "resolved"]
    persistent_issues = [h for h in correction_history if h["status"] == "persistent"]
    regressed_issues = [h for h in correction_history if h["status"] == "regressed"]

    iteration_summaries = []
    for it in loop_iterations:
        iteration_summaries.append(
            f"Attempt {it['attempt']}: "
            f"{it['corrections_raised']} raised, "
            f"{it['corrections_resolved']} resolved, "
            f"{it['corrections_new']} new, "
            f"{it['corrections_regressed']} regressed"
        )

    return {
        "urgency_level": urgency,
        "open_issues": open_issues,
        "resolved_issues": resolved_issues,
        "persistent_issues": persistent_issues,
        "regressed_issues": regressed_issues,
        "iteration_summaries": iteration_summaries,
        "total_resolved": len(resolved_issues),
        "total_open": len(open_issues) + len(persistent_issues) + len(regressed_issues),
        "attempt": attempt,
        "max_attempts": max_attempts,
    }
