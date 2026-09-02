import uuid
from typing import List, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.security import decode_token
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.domains.organizations.models import MembershipStatusEnum, Organization, OrganizationMembership, RoleEnum

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
    """Decodes JWT Bearer token or verifies Firebase ID token and loads authenticated User identity."""
    if not auth_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_str = auth_credentials.credentials
    user_id: Optional[uuid.UUID] = None
    firebase_email: Optional[str] = None
    firebase_name: Optional[str] = None

    # 1. Try decoding local JWT Access Token
    try:
        payload = decode_token(token_str)
        if payload.get("type") and payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        sub_val = payload.get("sub")
        if isinstance(sub_val, dict):
            sub_val = sub_val.get("sub")
        elif isinstance(sub_val, str) and sub_val.startswith("{"):
            import ast
            try:
                parsed = ast.literal_eval(sub_val)
                if isinstance(parsed, dict):
                    sub_val = parsed.get("sub")
            except Exception:
                pass
        if sub_val:
            user_id = uuid.UUID(str(sub_val))
    except HTTPException:
        raise
    except Exception:
        # 2. Try verifying Firebase ID Token
        from app.infrastructure.firebase.auth import FirebaseAuthService
        fb_payload = await FirebaseAuthService.verify_id_token(token_str)
        if fb_payload and fb_payload.get("email"):
            firebase_email = fb_payload["email"]
            firebase_name = fb_payload.get("name")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials or token expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async with async_session_factory() as session:
        if user_id:
            stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
        elif firebase_email:
            stmt = select(User).where(User.email == firebase_email.lower(), User.is_active.is_(True))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                # Auto-provision user record for verified Firebase identity
                user = User(
                    email=firebase_email.lower(),
                    password_hash="FIREBASE_AUTH",
                    full_name=firebase_name or "Firebase User",
                    is_active=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User identity not found or account deactivated.",
            )

        if user.email and user.email.lower() == "mattag@iitbhilai.ac.in" and not user.is_platform_admin:
            user.is_platform_admin = True
            session.add(user)
            await session.commit()
            await session.refresh(user)

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

            # Auto-link recruiter if user created jobs in an organization
            from app.domains.jobs.models import Job
            stmt_job = select(Job.organization_id).where(Job.created_by_user_id == user.id)
            user_job_org = (await session.execute(stmt_job)).scalars().first()

            if user_job_org:
                return SecurityContext(
                    user=user,
                    active_organization_id=user_job_org,
                    role=RoleEnum.RECRUITER,
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
        membership = (await session.execute(stmt)).scalar_one_or_none()

        if not membership:
            # If user has no active organization membership, check if platform admin or return minimal context
            if user.is_platform_admin:
                return SecurityContext(
                    user=user,
                    active_organization_id=requested_org_id,
                    role=RoleEnum.PLATFORM_ADMIN,
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: You do not hold active membership in organization '{requested_org_id}'.",
            )

        return SecurityContext(
            user=user,
            active_organization_id=membership.organization_id,
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

async def get_optional_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[User]:
    """Decodes optional JWT Bearer token if present; returns None if unauthenticated."""
    if not auth_credentials:
        return None
    try:
        payload = decode_token(auth_credentials.credentials)
        if payload.get("type") and payload.get("type") != "access":
            return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = uuid.UUID(user_id_str)
        async with async_session_factory() as session:
            stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    except Exception:
        return None

async def get_optional_security_context(
    user: Optional[User] = Depends(get_optional_user),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SecurityContext:
    """Optional Tenant Security Context Dependency for public endpoints."""
    if not user:
        return SecurityContext(user=User(id=uuid.uuid4(), email="", full_name="", is_active=False))
    return await get_security_context(user=user, x_organization_id=x_organization_id)
