from pydantic import BaseModel, Field
from typing import Literal


class SourceFact(BaseModel):
    fact_id: str = Field(description="Unique identifier for this fact")
    fact_key: str = Field(description="Short key like 'budget_limit' or 'deadline_q3'")
    value: str = Field(description="The extracted value")
    source_reference: str = Field(description="Quote or location from the transcript")
    category: Literal["decision", "requirement", "constraint"] = Field(
        description="Classification of the fact"
    )


class Gap(BaseModel):
    description: str = Field(description="What information is missing or unclear")
    severity: Literal["blocking", "warning", "info"] = Field(
        description="How critical this gap is"
    )


class IntakeInput(BaseModel):
    transcript: str
    rules: str


class IntakeOutput(BaseModel):
    facts: list[SourceFact] = Field(description="Extracted facts with source references")
    gaps: list[Gap] = Field(description="Identified gaps or missing information")
    conflicts: list[str] = Field(
        description="Any conflicts found between decisions or with rules",
        default_factory=list,
    )
