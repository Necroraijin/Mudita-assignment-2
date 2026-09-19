"""Tests for the loop engineering module."""
import pytest
from app.agents.loop_engine import (
    build_correction_history,
    detect_convergence,
    build_loop_iteration,
    compute_plan_diff,
    build_progressive_context,
)


class TestCorrectionHistory:
    def test_new_corrections_added_as_open(self):
        corrections = [
            {"issue": "Missing security review", "evidence": "Rule 1", "required_change": "Add task"},
        ]
        history = build_correction_history(corrections, [], attempt=1)

        assert len(history) == 1
        assert history[0]["status"] == "open"
        assert history[0]["raised_at_attempt"] == 1
        assert history[0]["resolved_at_attempt"] is None

    def test_resolved_when_correction_disappears(self):
        previous = [
            {
                "issue": "Missing security review",
                "evidence": "Rule 1",
                "required_change": "Add task",
                "related_task_ids": [],
                "raised_at_attempt": 1,
                "resolved_at_attempt": None,
                "status": "open",
            },
        ]
        # No corrections in new round -> previous is resolved
        history = build_correction_history([], previous, attempt=2)

        assert len(history) == 1
        assert history[0]["status"] == "resolved"
        assert history[0]["resolved_at_attempt"] == 2

    def test_persistent_after_multiple_attempts(self):
        previous = [
            {
                "issue": "Missing task",
                "evidence": "Rule 1",
                "required_change": "Add it",
                "related_task_ids": [],
                "raised_at_attempt": 1,
                "resolved_at_attempt": None,
                "status": "open",
            },
        ]
        # Same correction still present on attempt 3
        current = [{"issue": "Missing task", "evidence": "Rule 1", "required_change": "Add it"}]
        history = build_correction_history(current, previous, attempt=3)

        persistent = [h for h in history if h["issue"] == "Missing task"]
        assert len(persistent) == 1
        assert persistent[0]["status"] == "persistent"

    def test_new_and_existing_corrections_together(self):
        previous = [
            {
                "issue": "Issue A",
                "evidence": "E",
                "required_change": "C",
                "related_task_ids": [],
                "raised_at_attempt": 1,
                "resolved_at_attempt": None,
                "status": "open",
            },
        ]
        current = [
            {"issue": "Issue A", "evidence": "E", "required_change": "C"},
            {"issue": "Issue B", "evidence": "E2", "required_change": "C2"},
        ]
        history = build_correction_history(current, previous, attempt=2)

        issues = {h["issue"]: h for h in history}
        assert "Issue A" in issues
        assert "Issue B" in issues
        assert issues["Issue B"]["status"] == "open"
        assert issues["Issue B"]["raised_at_attempt"] == 2


class TestConvergenceDetection:
    def test_not_stalled_with_one_iteration(self):
        iterations = [{"corrections_raised": 3, "corrections_new": 3, "corrections_regressed": 0}]
        assert detect_convergence(iterations) is False

    def test_stalled_when_count_not_decreasing(self):
        iterations = [
            {"corrections_raised": 3, "corrections_new": 0, "corrections_regressed": 0},
            {"corrections_raised": 3, "corrections_new": 0, "corrections_regressed": 0},
        ]
        assert detect_convergence(iterations) is True

    def test_not_stalled_when_count_decreasing(self):
        iterations = [
            {"corrections_raised": 3, "corrections_new": 0, "corrections_regressed": 0},
            {"corrections_raised": 1, "corrections_new": 0, "corrections_regressed": 0},
        ]
        assert detect_convergence(iterations) is False

    def test_stalled_when_regressions_occur(self):
        iterations = [
            {"corrections_raised": 2, "corrections_new": 0, "corrections_regressed": 0},
            {"corrections_raised": 2, "corrections_new": 1, "corrections_regressed": 1},
        ]
        assert detect_convergence(iterations) is True


class TestPlanDiff:
    def test_initial_plan(self):
        plan = {"tasks": [{"task_id": "task_001", "description": "Do something"}]}
        diff = compute_plan_diff(None, plan)
        assert "Initial plan" in diff

    def test_added_task(self):
        prev = {"tasks": [{"task_id": "task_001", "description": "A"}]}
        curr = {"tasks": [
            {"task_id": "task_001", "description": "A"},
            {"task_id": "task_002", "description": "B"},
        ]}
        diff = compute_plan_diff(prev, curr)
        assert "ADDED task_002" in diff

    def test_removed_task(self):
        prev = {"tasks": [
            {"task_id": "task_001", "description": "A"},
            {"task_id": "task_002", "description": "B"},
        ]}
        curr = {"tasks": [{"task_id": "task_001", "description": "A"}]}
        diff = compute_plan_diff(prev, curr)
        assert "REMOVED task_002" in diff

    def test_modified_task(self):
        prev = {"tasks": [{"task_id": "task_001", "description": "A", "owner": None}]}
        curr = {"tasks": [{"task_id": "task_001", "description": "A", "owner": "Alice"}]}
        diff = compute_plan_diff(prev, curr)
        assert "MODIFIED task_001" in diff
        assert "owner" in diff

    def test_no_changes(self):
        plan = {"tasks": [{"task_id": "task_001", "description": "A"}]}
        diff = compute_plan_diff(plan, plan)
        assert "No changes" in diff


class TestProgressiveContext:
    def test_first_attempt_is_normal_urgency(self):
        ctx = build_progressive_context([], [], [], attempt=1, max_attempts=3)
        assert ctx["urgency_level"] == "normal"

    def test_penultimate_attempt_is_elevated(self):
        ctx = build_progressive_context([], [], [], attempt=2, max_attempts=3)
        assert ctx["urgency_level"] == "elevated"

    def test_final_attempt_is_final(self):
        ctx = build_progressive_context([], [], [], attempt=3, max_attempts=3)
        assert ctx["urgency_level"] == "final"

    def test_counts_open_and_resolved(self):
        history = [
            {"issue": "A", "status": "resolved", "raised_at_attempt": 1, "resolved_at_attempt": 2},
            {"issue": "B", "status": "open", "raised_at_attempt": 1},
            {"issue": "C", "status": "persistent", "raised_at_attempt": 1},
        ]
        ctx = build_progressive_context(history, [], [], attempt=3, max_attempts=3)
        assert ctx["total_resolved"] == 1
        assert ctx["total_open"] == 2
