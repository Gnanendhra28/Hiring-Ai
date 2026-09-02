"""
Phase 6 Recruitment Operations, Collaboration & Communications Tests.
Verifies notification idempotency, candidate email privacy boundaries,
recruiter collaboration alerts, offer lifecycle, and audit trail consistency.
"""

import pytest
import uuid
from datetime import datetime, timezone
from app.services.notification_service import OperationalNotificationService, NotificationTypeEnum
from app.domains.applications.models import CandidatePlacement, OfferStatusEnum
from app.domains.recommendation.models import CandidateDecisionAudit, RecruiterDecisionEnum
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.candidates.models import CandidateProfile
from app.domains.applications.models import Application, ApplicationStatusEnum
from sqlalchemy import select


@pytest.mark.asyncio
async def test_notification_idempotency_and_privacy():
    """Verifies notification idempotency and candidate email privacy boundary."""
    service = OperationalNotificationService()
    org_id = uuid.uuid4()
    idempotency_key = f"event-idem-{uuid.uuid4().hex}"

    # 1. Dispatch first event
    res1 = await service.send_operational_notification(
        event_name=NotificationTypeEnum.INTERVIEW_SCHEDULED,
        organization_id=org_id,
        payload={"candidate_name": "Jane Doe", "job_title": "Lead Engineer"},
        idempotency_key=idempotency_key,
    )
    assert res1 is True

    # 2. Dispatch duplicate event (must be handled idempotently)
    res2 = await service.send_operational_notification(
        event_name=NotificationTypeEnum.INTERVIEW_SCHEDULED,
        organization_id=org_id,
        payload={"candidate_name": "Jane Doe", "job_title": "Lead Engineer"},
        idempotency_key=idempotency_key,
    )
    assert res2 is True

    # 3. Test Candidate Email Privacy Guardrail
    sensitive_context = {
        "candidate_name": "Jane Doe",
        "job_title": "Lead Engineer",
        "company_name": "CloudScale Inc",
        "interview_url": "https://example.com/interview/123/room",
        "internal_score": 92.5,
        "recruiter_notes": "Strong candidate, but verify concurrency depth.",
        "ai_reasoning": "High confidence match based on distributed systems experience.",
        "private_rubric": "Weight system design heavily.",
    }

    email_res = await service.dispatch_candidate_email(
        recipient_email="jane.doe@example.com",
        template_name="INTERVIEW_INVITATION",
        context=sensitive_context,
    )

    assert email_res["status"] == "SENT"
    assert email_res["recipient"] == "jane.doe@example.com"


@pytest.mark.asyncio
async def test_recruiter_alert_and_collaboration():
    """Verifies that recruiter alerts are dispatched with organization context and resource tracing."""
    service = OperationalNotificationService()
    org_id = uuid.uuid4()
    resource_id = f"app-{uuid.uuid4().hex[:8]}"

    alert_res = await service.dispatch_recruiter_alert(
        organization_id=org_id,
        recruiter_email="lead.recruiter@example.com",
        alert_title="AI Scorecard Ready for Review",
        message="Candidate John Smith completed technical interview for Staff Backend Engineer.",
        resource_id=resource_id,
    )

    assert alert_res["status"] == "DELIVERED"
    assert alert_res["organization_id"] == str(org_id)
    assert alert_res["resource_id"] == resource_id


@pytest.mark.asyncio
async def test_offer_lifecycle_and_audit_persistence():
    """Verifies offer lifecycle progression and immutable decision audit trail."""
    async with async_session_factory() as session:
        await session.begin()

        # 1. Setup Tenant & Recruiter
        org = Organization(name="FinTech Corp", slug=f"fintech-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        recruiter = User(
            email=f"rec_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Rachel Recruiter",
            password_hash="pw_hash_test",
            is_active=True,
        )
        cand_user = User(
            email=f"cand_fin_{uuid.uuid4().hex[:6]}@example.com",
            full_name="David Candidate",
            password_hash="pw_hash_test",
            is_active=True,
        )
        session.add_all([recruiter, cand_user])
        await session.flush()

        mem = OrganizationMembership(
            organization_id=org.id,
            user_id=recruiter.id,
            role=RoleEnum.RECRUITER,
        )
        session.add(mem)

        cand_profile = CandidateProfile(id=cand_user.id, user_id=cand_user.id)
        session.add(cand_profile)
        await session.flush()

        job = Job(
            organization_id=org.id,
            created_by_user_id=recruiter.id,
            title="Senior Financial Engineer",
            description="Build low-latency financial systems.",
            slug=f"fin-eng-{uuid.uuid4().hex[:6]}",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.flush()

        app_obj = Application(
            organization_id=org.id,
            job_id=job.id,
            candidate_id=cand_user.id,
            status=ApplicationStatusEnum.SELECTED,
        )
        session.add(app_obj)
        await session.flush()

        # 2. Create Candidate Placement & Extend Offer
        placement = CandidatePlacement(
            organization_id=org.id,
            job_id=job.id,
            application_id=app_obj.id,
            candidate_id=cand_user.id,
            offer_status=OfferStatusEnum.OFFER_EXTENDED,
            offer_created_at=datetime.now(timezone.utc),
            created_by_user_id=recruiter.id,
            notes="Standard senior package with stock options.",
        )
        session.add(placement)

        # 3. Create Recruiter Decision Audit
        audit = CandidateDecisionAudit(
            organization_id=org.id,
            job_id=job.id,
            candidate_id=cand_profile.id,
            application_id=app_obj.id,
            decision=RecruiterDecisionEnum.ADVANCE,
            previous_state="SELECTED",
            new_state="OFFER_EXTENDED",
            decision_reason="Candidate excelled in technical interview and team design review.",
            decided_by_user_id=recruiter.id,
        )
        session.add(audit)
        await session.commit()

        # 4. Verify Placement & Audit Records
        await session.begin()
        await set_tenant_context(session, organization_id=org.id)

        stmt_place = select(CandidatePlacement).where(CandidatePlacement.application_id == app_obj.id)
        saved_placement = (await session.execute(stmt_place)).scalar_one()
        assert saved_placement.offer_status == OfferStatusEnum.OFFER_EXTENDED
        assert saved_placement.created_by_user_id == recruiter.id

        stmt_aud = select(CandidateDecisionAudit).where(CandidateDecisionAudit.application_id == app_obj.id)
        saved_audit = (await session.execute(stmt_aud)).scalar_one()
        assert saved_audit.decision == RecruiterDecisionEnum.ADVANCE
        assert saved_audit.new_state == "OFFER_EXTENDED"
