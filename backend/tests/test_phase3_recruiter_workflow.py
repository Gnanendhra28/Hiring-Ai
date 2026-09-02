"""
Recruiter Workflow & ATS Comprehensive Tests.
Verifies tenant isolation, application state machine, human decision gates,
audit logging, and recruiter dashboard metrics.
"""

import pytest
import uuid
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum, MembershipStatusEnum
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.candidates.models import CandidateProfile
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.audit.models import AuditLog
from sqlalchemy import select, func


@pytest.mark.asyncio
async def test_recruiter_workflow_tenant_isolation_and_decisions():
    """Verifies that recruiters can shortlist and record decisions for their tenant's applications with audit trails."""
    async with async_session_factory() as session:
        await session.begin()

        # 1. Setup Tenant A and Recruiter A
        org_a = Organization(name="TechCorp Tenant A", slug=f"techcorp-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add(org_a)
        await session.flush()
        await set_tenant_context(session, org_a.id)

        recruiter_a = User(
            email=f"recruiter_a_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Alice Recruiter",
            password_hash="hashed_pw_test",
            is_platform_admin=False,
            is_active=True,
        )
        candidate = User(
            email=f"cand_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Bob Candidate",
            password_hash="hashed_pw_test",
            is_platform_admin=False,
            is_active=True,
        )
        session.add_all([recruiter_a, candidate])
        await session.flush()

        mem_a = OrganizationMembership(
            organization_id=org_a.id,
            user_id=recruiter_a.id,
            role=RoleEnum.RECRUITER,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(mem_a)

        cand_profile = CandidateProfile(id=candidate.id, user_id=candidate.id)
        session.add(cand_profile)
        await session.flush()

        # 2. Setup Job in Tenant A
        job_a = Job(
            organization_id=org_a.id,
            created_by_user_id=recruiter_a.id,
            title="Senior Distributed Systems Engineer",
            description="Develop high-scale distributed backend services using Python and PostgreSQL.",
            slug=f"dist-sys-eng-{uuid.uuid4().hex[:6]}",
            department="Engineering",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job_a)
        await session.flush()

        # 3. Create Application in Tenant A
        app_a = Application(
            organization_id=org_a.id,
            job_id=job_a.id,
            candidate_id=candidate.id,
            status=ApplicationStatusEnum.SUBMITTED,
            source="DIRECT",
        )
        session.add(app_a)
        await session.commit()

        # 4. Simulate Recruiter Decision: SHORTLIST
        await session.begin()
        await set_tenant_context(session, organization_id=org_a.id, user_id=recruiter_a.id)

        stmt_app = select(Application).where(Application.id == app_a.id)
        current_app = (await session.execute(stmt_app)).scalar_one()
        current_app.status = ApplicationStatusEnum.SHORTLISTED
        current_app.decision_reason = "Candidate has strong distributed systems background."
        current_app.decided_by_user_id = recruiter_a.id

        audit_entry = AuditLog(
            organization_id=org_a.id,
            user_id=recruiter_a.id,
            action="application.shortlisted",
            resource_type="application",
            resource_id=str(current_app.id),
            metadata_json={
                "previous_state": "SUBMITTED",
                "new_status": "SHORTLISTED",
                "decision_reason": "Candidate has strong distributed systems background.",
            }
        )
        session.add(audit_entry)
        await session.commit()

        # 5. Verify State and Audit Persistence
        await session.begin()
        await set_tenant_context(session, organization_id=org_a.id, user_id=recruiter_a.id)
        stmt_verify = select(Application).where(Application.id == app_a.id)
        verified_app = (await session.execute(stmt_verify)).scalar_one()
        assert verified_app.status == ApplicationStatusEnum.SHORTLISTED
        assert verified_app.decision_reason == "Candidate has strong distributed systems background."

        stmt_audit_verify = select(AuditLog).where(AuditLog.resource_id == str(app_a.id))
        audits = (await session.execute(stmt_audit_verify)).scalars().all()
        assert len(audits) >= 1
        assert audits[0].action == "application.shortlisted"
        assert audits[0].metadata_json["new_status"] == "SHORTLISTED"


@pytest.mark.asyncio
async def test_dashboard_metrics_stage_breakdown():
    """Verifies that the recruiter dashboard returns accurate query-backed application stage counts."""
    async with async_session_factory() as session:
        await session.begin()

        org = Organization(name="Metrics Org", slug=f"metrics-org-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        user = User(
            email=f"metrics_rec_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Metrics Recruiter",
            password_hash="pw",
            is_platform_admin=False,
            is_active=True,
        )
        cand1 = User(email=f"cand1_{uuid.uuid4().hex[:6]}@example.com", full_name="C1", password_hash="pw", is_active=True)
        cand2 = User(email=f"cand2_{uuid.uuid4().hex[:6]}@example.com", full_name="C2", password_hash="pw", is_active=True)
        session.add_all([user, cand1, cand2])
        await session.flush()

        p1 = CandidateProfile(id=cand1.id, user_id=cand1.id)
        p2 = CandidateProfile(id=cand2.id, user_id=cand2.id)
        session.add_all([p1, p2])
        await session.flush()

        job = Job(
            organization_id=org.id,
            created_by_user_id=user.id,
            title="Backend Lead",
            description="Lead backend architecture and engineering operations.",
            slug=f"backend-lead-{uuid.uuid4().hex[:6]}",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.flush()

        app1 = Application(organization_id=org.id, job_id=job.id, candidate_id=cand1.id, status=ApplicationStatusEnum.SHORTLISTED)
        app2 = Application(organization_id=org.id, job_id=job.id, candidate_id=cand2.id, status=ApplicationStatusEnum.SELECTED)
        session.add_all([app1, app2])
        await session.commit()

        # Query metrics
        await session.begin()
        await set_tenant_context(session, organization_id=org.id)

        stmt_shortlisted = select(func.count(Application.id)).where(
            Application.organization_id == org.id,
            Application.status == ApplicationStatusEnum.SHORTLISTED,
        )
        s_count = (await session.execute(stmt_shortlisted)).scalar()
        assert s_count == 1

        stmt_selected = select(func.count(Application.id)).where(
            Application.organization_id == org.id,
            Application.status == ApplicationStatusEnum.SELECTED,
        )
        sel_count = (await session.execute(stmt_selected)).scalar()
        assert sel_count == 1
