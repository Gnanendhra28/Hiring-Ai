import enum
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin

class WorkflowStageEnum(str, enum.Enum):
    SHORTLIST = "SHORTLIST"
    ASSESSMENT_INVITATION = "ASSESSMENT_INVITATION"
    INTERVIEW_INVITATION = "INTERVIEW_INVITATION"
    REJECTION = "REJECTION"
    OFFER = "OFFER"

class CommunicationStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DELETED = "DELETED"

class Communication(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Communication entity for candidate emails.
    Requires explicit human approval (status == APPROVED) before delivery.
    Scoped by organization_id for recruiter RLS and candidate_id for candidate ownership isolation.
    """
    __tablename__ = "communications"
    __table_args__ = {"extend_existing": True}

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_stage: Mapped[WorkflowStageEnum] = mapped_column(
        SQLEnum(WorkflowStageEnum), nullable=False, index=True
    )
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CommunicationStatusEnum] = mapped_column(
        SQLEnum(CommunicationStatusEnum), default=CommunicationStatusEnum.DRAFT, nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), default="MAILPIT", nullable=False)
    validation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
