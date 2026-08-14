import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin

class InterviewTypeEnum(str, enum.Enum):
    TECHNICAL = "TECHNICAL"
    BEHAVIORAL = "BEHAVIORAL"
    HR = "HR"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"

class InterviewStatusEnum(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    RESCHEDULED = "RESCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class MeetingProviderEnum(str, enum.Enum):
    TEAMS = "TEAMS"
    ZOOM = "ZOOM"
    MEET = "MEET"
    TEST = "TEST"

class Interview(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Scheduled Interview session entity.
    Stores UTC timestamps, requested display timezone, candidate ID, and video meeting links.
    Scoped by organization_id for recruiter RLS and candidate_id for candidate ownership isolation.
    """
    __tablename__ = "interviews"
    __table_args__ = {"extend_existing": True}

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interview_type: Mapped[InterviewTypeEnum] = mapped_column(
        SQLEnum(InterviewTypeEnum), default=InterviewTypeEnum.TECHNICAL, nullable=False
    )
    scheduled_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    status: Mapped[InterviewStatusEnum] = mapped_column(
        SQLEnum(InterviewStatusEnum), default=InterviewStatusEnum.SCHEDULED, nullable=False, index=True
    )
    meeting_provider: Mapped[MeetingProviderEnum] = mapped_column(
        SQLEnum(MeetingProviderEnum), default=MeetingProviderEnum.TEST, nullable=False
    )
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
