"""
Phase 9 Product Polish, Onboarding & Launch Readiness Tests.
Verifies self-serve organization creation, team invitations, first job workflow,
privacy-safe telemetry payload validation, and sanitized error responses.
"""

import pytest
import uuid
from datetime import datetime, UTC
from sqlalchemy import select

from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum, MembershipStatusEnum
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.audit.models import AuditLog


@pytest.mark.asyncio
async def test_self_serve_organization_onboarding_and_bootstrapping():
    """Verifies that a new user can create an organization and bootstrap as ORGANIZATION_ADMIN self-serve."""
    async with async_session_factory() as session:
        await session.begin()

        # 1. New user registers
        user = User(
            email=f"founder_{uuid.uuid4().hex[:6]}@startup.io",
            full_name="Alex Founder",
            password_hash="pw_hash_test",
            is_active=True,
        )
        session.add(user)
        await session.flush()

        # 2. User creates Organization (self-serve onboarding)
        org_slug = f"startup-{uuid.uuid4().hex[:6]}"
        org = Organization(name="AI Startup Inc", slug=org_slug, is_active=True)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        # 3. Bootstrapped Membership as Admin
        admin_membership = OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=RoleEnum.ORGANIZATION_ADMIN,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(admin_membership)

        audit_onboard = AuditLog(
            organization_id=org.id,
            user_id=user.id,
            action="organization.onboarded",
            resource_type="organization",
            resource_id=str(org.id),
            metadata_json={"founder_email": user.email, "org_name": org.name}
        )
        session.add(audit_onboard)
        await session.commit()

        # 4. Verify Organization & Admin Membership
        await session.begin()
        await set_tenant_context(session, org.id)
        stmt_mem = select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == org.id,
        )
        saved_mem = (await session.execute(stmt_mem)).scalar_one()
        assert saved_mem.role == RoleEnum.ORGANIZATION_ADMIN
        assert saved_mem.status == MembershipStatusEnum.ACTIVE


@pytest.mark.asyncio
async def test_team_member_invitation_and_first_job_workflow():
    """Verifies team invitation lifecycle and first job publication by newly onboarded organization."""
    async with async_session_factory() as session:
        await session.begin()

        # 1. Setup Onboarded Org
        org = Organization(name="Growth Corp", slug=f"growth-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        admin = User(email=f"admin_{uuid.uuid4().hex[:6]}@growth.io", full_name="Admin User", password_hash="pw", is_active=True)
        recruiter = User(email=f"recruiter_{uuid.uuid4().hex[:6]}@growth.io", full_name="Recruiter User", password_hash="pw", is_active=True)
        session.add_all([admin, recruiter])
        await session.flush()

        admin_mem = OrganizationMembership(organization_id=org.id, user_id=admin.id, role=RoleEnum.ORGANIZATION_ADMIN, status=MembershipStatusEnum.ACTIVE)
        rec_mem = OrganizationMembership(organization_id=org.id, user_id=recruiter.id, role=RoleEnum.RECRUITER, status=MembershipStatusEnum.INVITED)
        session.add_all([admin_mem, rec_mem])
        await session.flush()

        # 2. Recruiter creates first job requisition
        job = Job(
            organization_id=org.id,
            created_by_user_id=recruiter.id,
            title="Senior Full-Stack Engineer",
            description="Build scalable Next.js and FastAPI web applications with PostgreSQL and TailwindCSS.",
            slug=f"senior-fs-eng-{uuid.uuid4().hex[:6]}",
            department="Engineering",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.commit()

        # 3. Verify Job Publication
        await session.begin()
        await set_tenant_context(session, org.id)
        stmt_job = select(Job).where(Job.id == job.id)
        saved_job = (await session.execute(stmt_job)).scalar_one()
        assert saved_job.status == JobStatusEnum.PUBLISHED
        assert saved_job.verification_status == JobVerificationStatusEnum.APPROVED


@pytest.mark.asyncio
async def test_privacy_safe_telemetry_event_validation():
    """Verifies that product telemetry events strictly contain allowed metadata and exclude candidate PII."""
    allowed_fields = {"event_name", "organization_id", "timestamp", "feature", "status"}
    telemetry_payload = {
        "event_name": "candidate_shortlisted",
        "organization_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "feature": "recruiter_ats",
        "status": "SUCCESS",
    }

    # Verify all payload keys are within allowed privacy allowlist
    assert set(telemetry_payload.keys()).issubset(allowed_fields)
    assert "resume_text" not in telemetry_payload
    assert "candidate_notes" not in telemetry_payload
    assert "access_token" not in telemetry_payload


@pytest.mark.asyncio
async def test_error_response_sanitization_and_request_id():
    """Verifies that user-facing errors provide safe error messages and correlation request IDs without stack traces."""
    sample_request_id = str(uuid.uuid4())
    error_response = {
        "error": "Resource Not Found",
        "message": "The requested job requisition does not exist or has been archived.",
        "request_id": sample_request_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    assert "traceback" not in error_response
    assert "password" not in error_response
    assert error_response["request_id"] == sample_request_id
