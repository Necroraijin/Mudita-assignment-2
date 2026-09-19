from pydantic import BaseModel, Field
from typing import Literal


class TaskItem(BaseModel):
    task_id: str = Field(description="Unique task identifier")
    description: str = Field(description="What needs to be done")
    owner: str | None = Field(
        default=None,
        description="Assigned owner (only if explicitly mentioned in transcript)",
    )
    deadline: str | None = Field(
        default=None,
        description="Deadline (only if explicitly mentioned in transcript)",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of tasks that must complete first",
    )
    source_fact_ids: list[str] = Field(
        default_factory=list,
        description="IDs of facts this task depends on",
    )
    item_type: Literal["fact", "recommendation", "open_question"] = Field(
        description="Whether this is grounded in fact, a recommendation, or an open question"
    )
    priority: Literal["high", "medium", "low"] = Field(default="medium")


class PlanningInput(BaseModel):
    facts: list[dict] = Field(description="Facts from Intake agent")
    gaps: list[dict] = Field(description="Gaps identified by Intake")
    conflicts: list[str] = Field(default_factory=list)
    rules: str = Field(description="Company rules to comply with")
    corrections: list[dict] = Field(
        default_factory=list,
        description="Corrections from Review agent (empty on first pass)",
    )


class PlanningOutput(BaseModel):
    tasks: list[TaskItem] = Field(description="Action items with owners and deadlines")
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made during planning",
    )
    open_questions: list[str] = Field(
        default_factory=list,
        description="Questions that need stakeholder input",
    )
    change_log: list[str] = Field(
        default_factory=list,
        description="What changed in this revision (empty on first pass)",
    )
