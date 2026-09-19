import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    intake_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    planning_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )
    review_attempt: Mapped[int] = mapped_column(default=0)
    simulated_failure_at: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    context_versions = relationship("ContextVersion", back_populates="run", cascade="all, delete-orphan")
    agent_outputs = relationship("AgentOutput", back_populates="run", cascade="all, delete-orphan")
    handoff_messages = relationship("HandoffMessage", back_populates="run", cascade="all, delete-orphan")
    review_cycles = relationship("ReviewCycle", back_populates="run", cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="run", cascade="all, delete-orphan")
