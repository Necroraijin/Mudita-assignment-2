from enum import Enum


class AgentName(str, Enum):
    INTAKE = "intake"
    PLANNING = "planning"
    REVIEW = "review"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    COMPLETED_WITH_ISSUES = "completed_with_issues"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"
