import uuid
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.security import decode_token
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.domains.organizations.models import MembershipStatusEnum, OrganizationMembership, RoleEnum

security_scheme = HTTPBearer(auto_error=False)

class SecurityContext:
    """
    Type-safe execution context holding verified authenticated user, active tenant, assigned role, and permissions.
    """
    def __init__(
        self,
        user: User,
        active_organization_id: Optional[uuid.UUID] = None,
        role: Optional[RoleEnum] = None,
        permissions: Optional[List[str]] = None,
    ) -> None:
        self.user = user
        self.active_organization_id = active_organization_id
        self.role = role
        self.permissions = permissions or []

    @property
    def is_platform_admin(self) -> bool:
        return self.user.is_platform_admin or self.role == RoleEnum.PLATFORM_ADMIN

async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> User:
    """Decodes JWT Bearer token and loads authenticated User identity."""
    if not auth_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(auth_credentials.credentials)
        if payload.get("type") and payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )
        user_id = uuid.UUID(user_id_str)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with async_session_factory() as session:
        stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity not found or account deactivated.",
            )
        return user

async def get_security_context(
    user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SecurityContext:
    """
    Core Tenant Authorization Dependency:
    Validates requested X-Organization-ID against active user memberships.
    NEVER trusts X-Organization-ID without membership verification.
    """
    if not x_organization_id:
        async with async_session_factory() as session:
            await session.begin()
            stmt = select(OrganizationMembership).where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.status == MembershipStatusEnum.ACTIVE,
            )
            result = await session.execute(stmt)
            membership = result.scalars().first()
            if membership:
                return SecurityContext(
                    user=user,
                    active_organization_id=membership.organization_id,
                    role=membership.role,
                )
        return SecurityContext(user=user)

    try:
        requested_org_id = uuid.UUID(x_organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for X-Organization-ID header.",
        )

    # Platform Admins bypass membership check if authorized
    if user.is_platform_admin:
        return SecurityContext(
            user=user,
            active_organization_id=requested_org_id,
            role=RoleEnum.PLATFORM_ADMIN,
        )

    # Verify active organization membership with transaction-scoped tenant context
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, requested_org_id)
        stmt = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == requested_org_id,
            OrganizationMembership.status == MembershipStatusEnum.ACTIVE,
        )
        result = await session.execute(stmt)
        membership = result.scalar_one_or_none()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: You do not hold active membership in organization '{requested_org_id}'.",
            )

        return SecurityContext(
            user=user,
            active_organization_id=requested_org_id,
            role=membership.role,
        )

def require_role(allowed_roles: List[RoleEnum]):
    """Role-Based Access Control (RBAC) Guard."""
    async def role_checker(ctx: SecurityContext = Depends(get_security_context)) -> SecurityContext:
        if ctx.user.is_platform_admin:
            return ctx
        if not ctx.role or ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role Access Denied: Action requires one of {[r.value for r in allowed_roles]}.",
            )
        return ctx
    return role_checker
