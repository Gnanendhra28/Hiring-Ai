import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin, UUIDMixin

class RecruiterProfile(Base, UUIDMixin, TimestampMixin):
    """
    Recruiter profile metadata extending User identity.
    """
    __tablename__ = "recruiter_profiles"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    registration_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="UNVERIFIED", nullable=False)
    submitted_at: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
