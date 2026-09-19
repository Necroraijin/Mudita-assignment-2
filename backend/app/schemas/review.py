from pydantic import BaseModel, Field
from typing import Literal


class ReviewCorrection(BaseModel):
    issue: str = Field(description="What is wrong with the plan")
    evidence: str = Field(description="Reference to transcript or rules that proves the issue")
    required_change: str = Field(description="What the Planning agent must change")
    related_task_ids: list[str] = Field(
        default_factory=list,
        description="Task IDs affected by this correction",
    )
    severity: Literal["critical", "major", "minor"] = Field(
        default="major",
        description="How severe the issue is",
    )
    is_new: bool = Field(
        default=True,
        description="Whether this is a newly discovered issue vs. a recurring one",
    )


class ReviewInput(BaseModel):
    transcript: str
    rules: str
    facts: list[dict]
    plan: dict
    attempt_number: int = 1


class ReviewOutput(BaseModel):
    approved: bool = Field(description="Whether the plan passes review")
    corrections: list[ReviewCorrection] = Field(
        default_factory=list,
        description="Structured corrections for Planning agent",
    )
    resolved_from_previous: list[str] = Field(
        default_factory=list,
        description="Issues successfully fixed in this revision",
    )
    unresolved_issues: list[str] = Field(
        default_factory=list,
        description="Issues that remain unresolved after max attempts",
    )
    summary: str = Field(description="Brief summary of review findings")
