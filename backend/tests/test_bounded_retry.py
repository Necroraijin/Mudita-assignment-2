import json
import pytest
from unittest.mock import patch, MagicMock
from app.agents.graph import compile_graph


def make_mock_llm_response(content_dict: dict):
    """Create a mock LLM response."""
    mock = MagicMock()
    mock.content = json.dumps(content_dict)
    mock.tokens_in = 100
    mock.tokens_out = 200
    mock.latency_ms = 500
    return mock


class TestBoundedRetry:
    @patch("app.agents.intake_agent.call_llm")
    @patch("app.agents.planning_agent.call_llm")
    @patch("app.agents.review_agent.call_llm")
    @patch("app.config.get_settings")
    def test_review_cap_reached(
        self, mock_settings, mock_review_llm, mock_planning_llm, mock_intake_llm
    ):
        """Review agent should stop after max_review_cycles attempts."""
        settings = MagicMock()
        settings.max_review_cycles = 2
        settings.gcp_project_id = "test-project"
        settings.gemini_api_key = "test-key"
        settings.gemini_model = "gemini-3.6-flash"
        mock_settings.return_value = settings

        # Intake always succeeds
        intake_response = make_mock_llm_response({
            "facts": [
                {
                    "fact_id": "fact_001",
                    "fact_key": "deadline",
                    "value": "Dec 15",
                    "source_reference": "line 1",
                    "category": "decision",
                }
            ],
            "gaps": [],
            "conflicts": [],
        })
        mock_intake_llm.return_value = intake_response

        # Planning always produces a plan
        planning_response = make_mock_llm_response({
            "tasks": [
                {
                    "task_id": "task_001",
                    "description": "Do something",
                    "owner": None,
                    "deadline": None,
                    "dependencies": [],
                    "source_fact_ids": ["fact_001"],
                    "item_type": "fact",
                    "priority": "high",
                }
            ],
            "assumptions": [],
            "open_questions": [],
        })
        mock_planning_llm.return_value = planning_response

        # Review always rejects (never approves)
        review_response = make_mock_llm_response({
            "approved": False,
            "corrections": [
                {
                    "issue": "Missing something",
                    "evidence": "Some evidence",
                    "required_change": "Add it",
                    "related_task_ids": ["task_001"],
                }
            ],
            "unresolved_issues": [],
            "summary": "Needs work",
        })
        mock_review_llm.return_value = review_response

        graph = compile_graph()
        initial_state = {
            "run_id": "test-run",
            "transcript": "test transcript",
            "rules": "test rules",
            "intake_output": None,
            "planning_output": None,
            "review_output": None,
            "review_attempt": 0,
            "corrections": [],
            "simulated_failure_at": None,
            "error": None,
            "status": "running",
        }

        final_state = initial_state
        for event in graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = {**final_state, **node_output}

        # Should have stopped at max_review_cycles
        assert final_state["review_attempt"] <= settings.max_review_cycles
        # Review called the LLM at most max_review_cycles times
        assert mock_review_llm.call_count <= settings.max_review_cycles
