from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_security_context, SecurityContext
from app.api.v1.schemas import (
    OrganizationMembershipResponse,
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.identity.models import User
from app.domains.organizations.models import MembershipStatusEnum, OrganizationMembership

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegisterRequest, request: Request):
    """Registers a new user identity."""
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == payload.email.lower())
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists.",
            )

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        audit = AuditLog(
            user_id=user.id,
            action="auth.register",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            correlation_id=getattr(request.state, "correlation_id", None),
        )
        session.add(audit)
        await session.commit()

        return user

@router.post("/login", response_model=TokenResponse)
async def login_user(payload: UserLoginRequest, request: Request):
    """Authenticates email/password and returns JWT access & refresh tokens."""
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == payload.email.lower())
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email address or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deactivated.",
            )

        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        audit = AuditLog(
            user_id=user.id,
            action="auth.login",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            correlation_id=getattr(request.state, "correlation_id", None),
        )
        session.add(audit)
        await session.commit()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.get("/me", response_model=UserProfileResponse)
async def get_user_profile(ctx: SecurityContext = Depends(get_security_context)):
    """
    Returns authenticated user profile and all active organization memberships.
    Evaluates SecurityContext dependency to verify X-Organization-ID membership if supplied.
    """
    user = ctx.user
    async with async_session_factory() as session:
        stmt = (
            select(OrganizationMembership)
            .options(selectinload(OrganizationMembership.organization))
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.status == MembershipStatusEnum.ACTIVE,
            )
        )
        result = await session.execute(stmt)
        memberships = list(result.scalars().all())

        membership_responses = [
            OrganizationMembershipResponse(
                id=m.id,
                organization_id=m.organization_id,
                organization_name=m.organization.name,
                organization_slug=m.organization.slug,
                role=m.role,
                status=m.status,
            )
            for m in memberships
        ]

        return UserProfileResponse(
            user=UserResponse.model_validate(user),
            memberships=membership_responses,
        )
