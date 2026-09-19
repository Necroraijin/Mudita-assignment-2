from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.config import get_settings


class RunCreate(BaseModel):
    transcript: str = Field(description="Meeting transcript text")
    rules: str = Field(description="Company rules/policies text")

    @field_validator("transcript")
    @classmethod
    def validate_transcript_length(cls, v: str) -> str:
        settings = get_settings()
        if len(v) > settings.max_transcript_length:
            raise ValueError(
                f"Transcript exceeds maximum length of {settings.max_transcript_length} characters"
            )
        if len(v.strip()) == 0:
            raise ValueError("Transcript cannot be empty")
        return v

    @field_validator("rules")
    @classmethod
    def validate_rules_length(cls, v: str) -> str:
        settings = get_settings()
        if len(v) > settings.max_rules_length:
            raise ValueError(
                f"Rules exceed maximum length of {settings.max_rules_length} characters"
            )
        if len(v.strip()) == 0:
            raise ValueError("Rules cannot be empty")
        return v


class RunListItem(BaseModel):
    id: str
    status: str
    intake_status: str
    planning_status: str
    review_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentOutputResponse(BaseModel):
    agent: str
    version: int
    payload_json: dict
    tokens_in: int | None = None
    tokens_out: int | None = None
    latency_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HandoffMessageResponse(BaseModel):
    from_agent: str
    to_agent: str
    content: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewCycleResponse(BaseModel):
    attempt_number: int
    corrections: dict
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ActionLogResponse(BaseModel):
    actor: str
    action: str
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FactResponse(BaseModel):
    id: str
    fact_key: str
    value: str
    source_reference: str
    category: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RunDetailResponse(BaseModel):
    id: str
    transcript: str
    rules: str
    status: str
    intake_status: str
    planning_status: str
    review_status: str
    review_attempt: int
    error: str | None
    created_at: datetime
    updated_at: datetime
    agent_outputs: list[AgentOutputResponse]
    handoff_messages: list[HandoffMessageResponse]
    review_cycles: list[ReviewCycleResponse]
    action_logs: list[ActionLogResponse]
    facts: list[FactResponse]


class FactUpdateRequest(BaseModel):
    value: str = Field(description="Corrected fact value")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str) -> str:
        if len(v.strip()) == 0:
            raise ValueError("Fact value cannot be empty")
        return v


class SimulateFailureRequest(BaseModel):
    step: str = Field(description="Which agent step to fail: intake, planning, or review")

    @field_validator("step")
    @classmethod
    def validate_step(cls, v: str) -> str:
        valid = {"intake", "planning", "review"}
        if v not in valid:
            raise ValueError(f"Step must be one of: {', '.join(valid)}")
        return v
