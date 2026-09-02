import uuid
from typing import Any
from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin, UUIDMixin

class CandidateProfile(Base, UUIDMixin, TimestampMixin):
    """
    Candidate professional profile metadata extending User identity.
    A candidate user can apply across multiple organization jobs without becoming an org member.
    """
    __tablename__ = "candidate_profiles"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True, default=list)
    experience: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    education: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    career_preferences: Mapped[Any | None] = mapped_column(JSON, nullable=True, default=dict)
    languages: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    internships: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    projects: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    accomplishments: Mapped[Any | None] = mapped_column(JSON, nullable=True, default=dict)
    employment: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, default=list)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_filesize: Mapped[int | None] = mapped_column(nullable=True)
    resume_updated_at: Mapped[str | None] = mapped_column(String(100), nullable=True)
