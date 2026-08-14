import enum
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Enum as SQLEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.domains.identity.models import User

class RoleEnum(str, enum.Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    RECRUITER = "RECRUITER"
    CANDIDATE = "CANDIDATE"

class MembershipStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INVITED = "INVITED"

class OrganizationVerificationStatusEnum(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class Organization(Base, UUIDMixin, TimestampMixin):
    """
    Organization entity representing a SaaS tenant.
    """
    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    verification_status: Mapped[OrganizationVerificationStatusEnum] = mapped_column(
        SQLEnum(OrganizationVerificationStatusEnum),
        default=OrganizationVerificationStatusEnum.UNVERIFIED,
        nullable=False,
    )

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        "OrganizationMembership", back_populates="organization", cascade="all, delete-orphan"
    )

class OrganizationMembership(Base, UUIDMixin, TimestampMixin):
    """
    Dynamic User -> Organization Membership link defining assigned roles & status per organization tenant.
    """
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_organization_user_membership"),
        {"extend_existing": True},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[RoleEnum] = mapped_column(
        SQLEnum(RoleEnum), default=RoleEnum.RECRUITER, nullable=False
    )
    status: Mapped[MembershipStatusEnum] = mapped_column(
        SQLEnum(MembershipStatusEnum), default=MembershipStatusEnum.ACTIVE, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")
