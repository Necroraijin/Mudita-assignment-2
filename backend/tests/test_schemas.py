import pytest
from pydantic import ValidationError
from app.schemas.intake import IntakeOutput, SourceFact, Gap
from app.schemas.planning import PlanningOutput, TaskItem
from app.schemas.review import ReviewOutput, ReviewCorrection


class TestIntakeSchema:
    def test_valid_intake_output(self):
        data = {
            "facts": [
                {
                    "fact_id": "fact_001",
                    "fact_key": "deadline",
                    "value": "December 15th",
                    "source_reference": "We need to launch by December 15th",
                    "category": "decision",
                }
            ],
            "gaps": [
                {"description": "No rollback plan mentioned", "severity": "warning"}
            ],
            "conflicts": [],
        }
        output = IntakeOutput(**data)
        assert len(output.facts) == 1
        assert output.facts[0].fact_key == "deadline"

    def test_invalid_category_rejected(self):
        data = {
            "facts": [
                {
                    "fact_id": "fact_001",
                    "fact_key": "test",
                    "value": "test",
                    "source_reference": "test",
                    "category": "invalid_category",
                }
            ],
            "gaps": [],
            "conflicts": [],
        }
        with pytest.raises(ValidationError):
            IntakeOutput(**data)

    def test_invalid_severity_rejected(self):
        data = {
            "facts": [],
            "gaps": [{"description": "test", "severity": "critical"}],
            "conflicts": [],
        }
        with pytest.raises(ValidationError):
            IntakeOutput(**data)


class TestPlanningSchema:
    def test_valid_planning_output(self):
        data = {
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Build dashboard",
                    "owner": "Alex",
                    "deadline": "December 15th",
                    "dependencies": [],
                    "source_fact_ids": ["fact_001"],
                    "item_type": "fact",
                    "priority": "high",
                }
            ],
            "assumptions": ["Team has capacity"],
            "open_questions": [],
        }
        output = PlanningOutput(**data)
        assert len(output.tasks) == 1
        assert output.tasks[0].owner == "Alex"

    def test_null_owner_deadline_allowed(self):
        data = {
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Something",
                    "owner": None,
                    "deadline": None,
                    "dependencies": [],
                    "source_fact_ids": [],
                    "item_type": "recommendation",
                    "priority": "low",
                }
            ],
            "assumptions": [],
            "open_questions": [],
        }
        output = PlanningOutput(**data)
        assert output.tasks[0].owner is None

    def test_invalid_item_type_rejected(self):
        data = {
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Something",
                    "item_type": "unknown",
                    "priority": "high",
                }
            ],
            "assumptions": [],
            "open_questions": [],
        }
        with pytest.raises(ValidationError):
            PlanningOutput(**data)


class TestReviewSchema:
    def test_approved_review(self):
        data = {
            "approved": True,
            "corrections": [],
            "unresolved_issues": [],
            "summary": "Plan looks good.",
        }
        output = ReviewOutput(**data)
        assert output.approved is True
        assert len(output.corrections) == 0

    def test_review_with_corrections(self):
        data = {
            "approved": False,
            "corrections": [
                {
                    "issue": "Missing security review task",
                    "evidence": "Rule 1: All deployments require security review",
                    "required_change": "Add security review task before deployment",
                    "related_task_ids": ["task_003"],
                }
            ],
            "unresolved_issues": [],
            "summary": "Plan missing required security step.",
        }
        output = ReviewOutput(**data)
        assert output.approved is False
        assert len(output.corrections) == 1
        assert output.corrections[0].issue == "Missing security review task"

    def test_missing_summary_rejected(self):
        data = {
            "approved": True,
            "corrections": [],
            "unresolved_issues": [],
        }
        with pytest.raises(ValidationError):
            ReviewOutput(**data)
