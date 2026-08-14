from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_user
from app.api.v1.schemas import OrganizationCreateRequest, OrganizationMembershipResponse, OrganizationResponse
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.identity.models import User
from app.domains.organizations.models import (
    MembershipStatusEnum,
    Organization,
    OrganizationMembership,
    RoleEnum,
)

router = APIRouter(prefix="/organizations", tags=["Organizations & Tenants"])

@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_organization(
    payload: OrganizationCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Creates a new Organization tenant and bootstraps current user as ORGANIZATION_ADMIN."""
    async with async_session_factory() as session:
        await session.begin()
        # Check slug uniqueness
        stmt = select(Organization).where(Organization.slug == payload.slug.lower())
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization slug '{payload.slug}' is already taken.",
            )

        org = Organization(
            name=payload.name,
            slug=payload.slug.lower(),
        )
        session.add(org)
        await session.flush()

        # Set transaction RLS context for new organization
        await set_tenant_context(session, org.id)

        # Bootstrap Admin Membership
        membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=RoleEnum.ORGANIZATION_ADMIN,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(membership)

        # Audit Log
        audit = AuditLog(
            organization_id=org.id,
            user_id=user.id,
            action="organization.create",
            resource_type="organization",
            resource_id=str(org.id),
            ip_address=request.client.host if request.client else None,
            correlation_id=getattr(request.state, "correlation_id", None),
        )
        session.add(audit)
        await session.commit()
        await session.refresh(org)

        return org

@router.get("/me", response_model=List[OrganizationMembershipResponse])
async def list_my_organization_memberships(user: User = Depends(get_current_user)):
    """Returns list of organizations where current authenticated user holds active membership."""
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

        return [
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
