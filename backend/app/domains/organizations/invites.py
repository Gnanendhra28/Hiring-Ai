import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TenantMixin, TimestampMixin, UUIDMixin
from app.domains.organizations.models import RoleEnum

class OrganizationInvite(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Organization team member invitation record.
    """
    __tablename__ = "organization_invites"
    __table_args__ = {"extend_existing": True}

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum), default=RoleEnum.RECRUITER, nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    invited_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
