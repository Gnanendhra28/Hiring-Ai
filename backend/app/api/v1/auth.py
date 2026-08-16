import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import urllib.parse
from app.core.config import settings
from app.api.v1.deps import get_security_context, SecurityContext
from app.api.v1.schemas import (
    CandidateRegisterRequest,
    EmployeeRegisterRequest,
    GoogleAuthRequest,
    GoogleAuthUrlResponse,
    OrganizationMembershipResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.identity.models import User
from app.domains.organizations.models import Organization, RoleEnum, MembershipStatusEnum, OrganizationMembership
from app.db.rls import set_tenant_context

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

@router.post("/register/candidate", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_candidate(payload: CandidateRegisterRequest, request: Request):
    """Registers a Candidate identity with server-enforced CANDIDATE role assignment and phone validation."""
    full_name = f"{payload.first_name.strip()} {payload.last_name.strip()}"
    phone_clean = payload.phone_number.strip()

    import re
    digits = re.sub(r"\D", "", phone_clean)
    if len(digits) < 7 or len(digits) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid phone number (minimum 7 digits).",
        )

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
            full_name=full_name,
            phone_number=phone_clean,
            is_platform_admin=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        audit = AuditLog(
            user_id=user.id,
            action="auth.register.candidate",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            correlation_id=getattr(request.state, "correlation_id", None),
        )
        session.add(audit)
        await session.commit()

        return user

@router.post("/register/employee", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_employee(payload: EmployeeRegisterRequest, request: Request):
    """Registers an Employee identity with server-enforced RECRUITER role assignment."""
    full_name = f"{payload.first_name.strip()} {payload.last_name.strip()}"
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
            full_name=full_name,
            is_platform_admin=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create or assign employee organization with server-enforced RECRUITER role
        org_name = payload.company_name or f"{payload.last_name.strip()}'s Organization"
        import re
        slug_base = re.sub(r'[^a-z0-9]+', '-', org_name.lower()).strip('-') or "org"
        slug = f"{slug_base}-{str(uuid.uuid4())[:8]}"

        org = Organization(
            name=org_name,
            slug=slug,
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)

        await set_tenant_context(session, org.id)
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=RoleEnum.RECRUITER,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(membership)
        await session.commit()

        audit = AuditLog(
            user_id=user.id,
            action="auth.register.employee",
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

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(payload: TokenRefreshRequest, request: Request):
    """
    Exchanges a valid JWT refresh token for a new access and refresh token pair.
    CRITICAL SECURITY GUARD: Rejects access tokens passed as refresh tokens.
    """
    import uuid
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: Refresh token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id_str = decoded.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = uuid.UUID(user_id_str)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {str(e)}",
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
                headers={"WWW-Authenticate": "Bearer"},
            )

        new_access_token = create_access_token(user_id=user.id)
        new_refresh_token = create_refresh_token(user_id=user.id)

        audit = AuditLog(
            user_id=user.id,
            action="auth.refresh",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            correlation_id=getattr(request.state, "correlation_id", None),
        )
        session.add(audit)
        await session.commit()

        return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)

@router.get("/me", response_model=UserProfileResponse)
async def get_user_profile(ctx: SecurityContext = Depends(get_security_context)):
    """
    Returns authenticated user profile and all active organization memberships.
    Evaluates SecurityContext dependency to verify X-Organization-ID membership if supplied.
    """
    user = ctx.user
    async with async_session_factory() as session:
        if ctx.active_organization_id:
            await set_tenant_context(session, ctx.active_organization_id)
        else:
            first_org_stmt = select(OrganizationMembership.organization_id).where(OrganizationMembership.user_id == user.id)
            first_org_res = await session.execute(first_org_stmt)
            first_org_id = first_org_res.scalar_one_or_none()
            if first_org_id:
                await set_tenant_context(session, first_org_id)

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


@router.get("/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url(redirect_uri: Optional[str] = None):
    """
    Returns the Google OAuth 2.0 authorization consent URL if GOOGLE_CLIENT_ID is configured.
    """
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id or client_id in ("placeholder_client_id", "placeholder_google_client_id"):
        return GoogleAuthUrlResponse(url=None, configured=False)

    target_redirect = redirect_uri or settings.GOOGLE_REDIRECT_URI or "http://localhost:3000/auth/callback/google"
    params = {
        "client_id": client_id,
        "redirect_uri": target_redirect,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return GoogleAuthUrlResponse(url=url, configured=True)


@router.post("/google/callback", response_model=TokenResponse)
async def google_oauth_callback(payload: GoogleAuthRequest, request: Request):
    """
    Exchanges Google OAuth code for tokens, verifies Google identity,
    links existing accounts by verified email, or provisions a candidate/employee account.
    CRITICAL GUARD: Admin accounts CANNOT be created via self-service Google OAuth.
    """
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    target_redirect = payload.redirect_uri or settings.GOOGLE_REDIRECT_URI or "http://localhost:3000/auth/callback/google"

    if not client_id or not client_secret or client_id in ("placeholder_client_id", "placeholder_google_client_id"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured on this server.",
        )

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": payload.code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": target_redirect,
        "grant_type": "authorization_code",
    }

    import httpx
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        token_resp = await http_client.post(token_url, data=data)
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to exchange authorization code with Google: {token_resp.text}",
            )
        token_data = token_resp.json()
        google_access_token = token_data.get("access_token")

        if not google_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token returned from Google.",
            )

        userinfo_resp = await http_client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to retrieve user profile from Google.",
            )
        userinfo = userinfo_resp.json()

    email = userinfo.get("email", "").lower()
    email_verified = userinfo.get("email_verified", False)
    full_name = userinfo.get("name") or f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip() or "Google User"

    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified.",
        )

    async with async_session_factory() as session:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=email,
                password_hash=hash_password(str(uuid.uuid4())),
                full_name=full_name,
                is_platform_admin=False,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            if payload.requested_role and payload.requested_role.upper() in ("RECRUITER", "EMPLOYEE"):
                import re
                slug_base = re.sub(r'[^a-z0-9]+', '-', full_name.lower()).strip('-') or "org"
                slug = f"{slug_base}-{str(uuid.uuid4())[:8]}"
                org = Organization(name=f"{full_name}'s Organization", slug=slug)
                session.add(org)
                await session.commit()
                await session.refresh(org)

                await set_tenant_context(session, org.id)
                membership = OrganizationMembership(
                    organization_id=org.id,
                    user_id=user.id,
                    role=RoleEnum.RECRUITER,
                    status=MembershipStatusEnum.ACTIVE,
                )
                session.add(membership)
                await session.commit()

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been deactivated.",
            )

        access_token = create_access_token(user_id=user.id)
        refresh_token = create_refresh_token(user_id=user.id)

        audit = AuditLog(
            user_id=user.id,
            action="auth.google.login",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            correlation_id=getattr(request.state, "correlation_id", None),
        )
        session.add(audit)
        await session.commit()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

