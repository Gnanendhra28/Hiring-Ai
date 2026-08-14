import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin

class JobStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"

class JobVerificationStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class EmploymentTypeEnum(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"

class Job(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Job entity representing a job posting within an organization tenant context.
    Requires Platform Admin approval (verification_status == APPROVED) before publication.
    Protected by PostgreSQL Row Level Security (RLS).
    """
    __tablename__ = "jobs"
    __table_args__ = {"extend_existing": True}

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[EmploymentTypeEnum] = mapped_column(
        SQLEnum(EmploymentTypeEnum), default=EmploymentTypeEnum.FULL_TIME, nullable=False
    )
    status: Mapped[JobStatusEnum] = mapped_column(
        SQLEnum(JobStatusEnum), default=JobStatusEnum.DRAFT, nullable=False, index=True
    )
    verification_status: Mapped[JobVerificationStatusEnum] = mapped_column(
        SQLEnum(JobVerificationStatusEnum), default=JobVerificationStatusEnum.DRAFT, nullable=False, index=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
