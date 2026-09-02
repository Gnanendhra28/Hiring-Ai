import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization, OrganizationMembership, RoleEnum
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, EmploymentTypeEnum
from app.domains.applications.models import Application, ApplicationStatusEnum, CandidatePlacement, OfferStatusEnum
from app.domains.candidates.models import CandidateProfile
from app.domains.recommendation.models import CandidateDecisionAudit, CandidateRecommendation, RecruiterDecisionEnum, ReviewStateEnum
from app.domains.scoring.models import CandidateJobScore
from app.core.security import create_access_token
from app.events.integration_events import CandidateHiredEvent, OfferAcceptedEvent, OfferCreatedEvent, JobIntelligenceCompletedEvent
from app.services.notification_service import OperationalNotificationService

@pytest.mark.asyncio
async def test_phase19_organization_dashboard_and_reporting():
    async with async_session_factory() as session:
        await session.begin()
        
        # 1. Create Organization
        slug = f"org-p19-{uuid.uuid4().hex[:6]}"
        org = Organization(name=f"Enterprise Org {uuid.uuid4().hex[:6]}", slug=slug)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        # 2. Create Users
        recruiter = User(email=f"recruiter_p19_{uuid.uuid4().hex[:6]}@example.com", password_hash="hashed_pass_123", full_name="Recruiter User")
        candidate_user = User(email=f"cand_p19_{uuid.uuid4().hex[:6]}@example.com", password_hash="hashed_pass_123", full_name="Candidate User")
        session.add_all([recruiter, candidate_user])
        await session.flush()

        mem = OrganizationMembership(organization_id=org.id, user_id=recruiter.id, role=RoleEnum.RECRUITER)
        session.add(mem)

        cand_profile = CandidateProfile(id=candidate_user.id, user_id=candidate_user.id)
        session.add(cand_profile)
        await session.flush()

        # 3. Create Jobs
        j1 = Job(
            organization_id=org.id,
            title="Senior Platform Engineer",
            slug=f"job-spe-{uuid.uuid4().hex[:6]}",
            department="Engineering",
            location="Remote",
            employment_type=EmploymentTypeEnum.FULL_TIME,
            status=JobStatusEnum.PUBLISHED,
            description="Leading platform architecture",
        )
        j2 = Job(
            organization_id=org.id,
            title="Lead Frontend Developer",
            slug=f"job-lfd-{uuid.uuid4().hex[:6]}",
            department="Engineering",
            location="New York",
            employment_type=EmploymentTypeEnum.FULL_TIME,
            status=JobStatusEnum.CLOSED,
            description="Job description",
        )
        session.add_all([j1, j2])
        await session.flush()

        # 4. Create Application & Placement for closed job (Time to fill)
        app_obj = Application(
            organization_id=org.id,
            job_id=j2.id,
            candidate_id=candidate_user.id,
            status=ApplicationStatusEnum.OFFER,
        )
        session.add(app_obj)
        await session.flush()

        placement = CandidatePlacement(
            organization_id=org.id,
            job_id=j2.id,
            application_id=app_obj.id,
            candidate_id=candidate_user.id,
            offer_status=OfferStatusEnum.HIRED,
            created_by_user_id=recruiter.id,
            placed_at=j2.created_at + timedelta(days=12),
        )
        session.add(placement)
        await session.commit()

        token = create_access_token(recruiter.id)

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id),
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # A. Organization Dashboard
        res_dash = await client.get("/api/v1/requisitions/dashboard", headers=headers)
        assert res_dash.status_code == 200
        data_dash = res_dash.json()
        assert data_dash["total_requisitions"] == 2
        assert data_dash["published_requisitions"] == 1
        assert data_dash["closed_requisitions"] == 1
        assert data_dash["filled_requisitions"] == 1
        assert data_dash["candidates_hired"] == 1
        assert data_dash["avg_time_to_fill_days"] == 12.0
        assert len(data_dash["requisitions"]) == 2

        # B. Dashboard Status Filter
        res_filt = await client.get("/api/v1/requisitions/dashboard?status=PUBLISHED", headers=headers)
        assert res_filt.status_code == 200
        assert res_filt.json()["total_requisitions"] == 1
        assert res_filt.json()["requisitions"][0]["title"] == "Senior Platform Engineer"

        # C. Audit Analytics
        res_audit = await client.get("/api/v1/requisitions/audit-analytics", headers=headers)
        assert res_audit.status_code == 200
        data_audit = res_audit.json()
        assert data_audit["candidate_hired_count"] == 1
        assert data_audit["audit_trail_completeness_pct"] == 100.0

        # D. AI Governance Analytics
        res_gov = await client.get("/api/v1/requisitions/ai-governance-analytics", headers=headers)
        assert res_gov.status_code == 200
        data_gov = res_gov.json()
        assert data_gov["ai_decision_authority"] == "HUMAN_RECRUITER_ONLY_0_PERCENT_AI_MUTATION"

        # E. AI Telemetry
        res_tel = await client.get("/api/v1/requisitions/ai-telemetry", headers=headers)
        assert res_tel.status_code == 200
        assert res_tel.json()["successful_requests"] >= 0

        # F. Organization CSV Export
        res_csv = await client.get("/api/v1/requisitions/report/export", headers=headers)
        assert res_csv.status_code == 200
        assert "Organization Summary" in res_csv.text
        assert "Senior Platform Engineer" in res_csv.text

@pytest.mark.asyncio
async def test_phase19_security_and_tenant_isolation():
    async with async_session_factory() as session:
        await session.begin()

        org1 = Organization(name=f"Org A {uuid.uuid4().hex[:6]}", slug=f"org-a-{uuid.uuid4().hex[:6]}")
        org2 = Organization(name=f"Org B {uuid.uuid4().hex[:6]}", slug=f"org-b-{uuid.uuid4().hex[:6]}")
        session.add_all([org1, org2])
        await session.flush()

        await set_tenant_context(session, org1.id)

        recruiter1 = User(email=f"rec1_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="Recruiter One")
        session.add(recruiter1)
        await session.flush()

        mem1 = OrganizationMembership(organization_id=org1.id, user_id=recruiter1.id, role=RoleEnum.RECRUITER)
        session.add(mem1)

        job1 = Job(
            organization_id=org1.id,
            title="Org A Job",
            slug=f"job-orga-{uuid.uuid4().hex[:6]}",
            employment_type=EmploymentTypeEnum.FULL_TIME,
            status=JobStatusEnum.PUBLISHED,
            description="Job for org A",
        )
        session.add(job1)
        await session.commit()

        token1 = create_access_token(recruiter1.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Anonymous -> 401
        res_anon = await client.get("/api/v1/requisitions/dashboard")
        assert res_anon.status_code == 401

        # Missing Organization Header -> 400 or 403
        res_no_org = await client.get("/api/v1/requisitions/dashboard", headers={"Authorization": f"Bearer {token1}"})
        assert res_no_org.status_code in [400, 403]

        # Cross-Tenant Header -> 403 or 404
        res_cross = await client.get(
            f"/api/v1/requisitions/{job1.id}/report",
            headers={"Authorization": f"Bearer {token1}", "X-Organization-ID": str(org2.id)},
        )
        assert res_cross.status_code in [403, 404]

@pytest.mark.asyncio
async def test_ranking_heartbeat_route_behavior():
    async with async_session_factory() as session:
        await session.begin()

        org = Organization(name=f"Heartbeat Org {uuid.uuid4().hex[:6]}", slug=f"org-hb-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        user = User(email=f"hb_user_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass", full_name="HB User")
        session.add(user)
        await session.flush()

        mem = OrganizationMembership(organization_id=org.id, user_id=user.id, role=RoleEnum.RECRUITER)
        session.add(mem)

        job = Job(
            organization_id=org.id,
            title="Heartbeat Job",
            slug=f"job-hb-{uuid.uuid4().hex[:6]}",
            employment_type=EmploymentTypeEnum.FULL_TIME,
            status=JobStatusEnum.PUBLISHED,
            description="Heartbeat job",
        )
        session.add(job)
        await session.commit()

        token = create_access_token(user.id)

    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"/api/v1/jobs/{job.id}/ranking", headers=headers)
        # 200 OK with empty items or 404 when unranked
        assert res.status_code in [200, 404]
        if res.status_code == 200:
            assert res.json()["total"] == 0

@pytest.mark.asyncio
async def test_integration_events_and_notification_service():
    # 1. Test Event Payload Safety
    evt = CandidateHiredEvent(
        event_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
        application_id=uuid.uuid4(),
        candidate_id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        time_to_fill_days=10.5,
    )
    payload = evt.model_dump()
    assert "password" not in payload
    assert "jwt" not in payload
    assert "raw_resume_text" not in payload

    # 2. Test Notification Service Mocking
    notifier = OperationalNotificationService()
    sent = await notifier.send_operational_notification(
        event_name="candidate.hired",
        organization_id=evt.organization_id,
        payload=payload,
    )
    assert sent is True
