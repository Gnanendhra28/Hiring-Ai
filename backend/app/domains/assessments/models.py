import enum
import uuid
from datetime import datetime, UTC
from typing import Any
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin

class AssessmentAssignmentStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    SENT = "SENT"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class Assessment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Assessment template configured for a job requisition.
    Scoped by organization_id for recruiter RLS tenant isolation.
    """
    __tablename__ = "assessments"
    __table_args__ = {"extend_existing": True}

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)

class AssessmentAssignment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Assessment assignment issued to a specific candidate application.
    Scoped by organization_id for recruiter RLS and candidate_id for candidate ownership isolation.
    """
    __tablename__ = "assessment_assignments"
    __table_args__ = {"extend_existing": True}

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[AssessmentAssignmentStatusEnum] = mapped_column(
        SQLEnum(AssessmentAssignmentStatusEnum), default=AssessmentAssignmentStatusEnum.DRAFT, nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class AssessmentResult(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Assessment completion result submitted by candidate or assessment engine adapter.
    """
    __tablename__ = "assessment_results"
    __table_args__ = {"extend_existing": True}

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_assignments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(default=False, nullable=False)
    result_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
