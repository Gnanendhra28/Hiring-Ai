import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin

class ApplicationStatusEnum(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    RECRUITER_REVIEW = "RECRUITER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    # Extensible states for future phases
    ASSESSMENT = "ASSESSMENT"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    HIRED = "HIRED"

class Application(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Job application submission entity.
    Scoped by organization_id for recruiter RLS tenant isolation,
    and by candidate_id for candidate ownership authorization.
    """
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_application"),
        {"extend_existing": True},
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ApplicationStatusEnum] = mapped_column(
        SQLEnum(ApplicationStatusEnum), default=ApplicationStatusEnum.SUBMITTED, nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(50), default="DIRECT", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resume_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    answers_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    decided_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
