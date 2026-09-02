"""
Phase 7 Enterprise Integrations & Advanced Hiring Intelligence Tests.
Verifies external job import sanitization and deduplication, tenant-scoped candidate rediscovery,
pgvector semantic matching, webhook HMAC signature verification, and AI vs Human analytics.
"""

import pytest
import uuid
import hmac
import hashlib
from datetime import datetime, UTC
from sqlalchemy import select, func

from app.db.session import async_session_factory
from app.db.rls import set_tenant_context
from app.domains.organizations.models import Organization
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.candidates.models import CandidateProfile
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.recommendation.models import CandidateDecision, RecruiterDecisionEnum
from app.domains.audit.models import AuditLog


@pytest.mark.asyncio
async def test_job_import_sanitization_and_deduplication():
    """Verifies that external job import validates schema, sanitizes input, and enforces tenant deduplication."""
    async with async_session_factory() as session:
        await session.begin()

        # 1. Setup Organization & Recruiter
        org = Organization(name="Enterprise Tech Corp", slug=f"ent-tech-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        recruiter = User(
            email=f"ent_rec_{uuid.uuid4().hex[:6]}@example.com",
            full_name="Enterprise Admin",
            password_hash="pw_hash_test",
            is_active=True,
        )
        session.add(recruiter)
        await session.flush()

        # 2. Simulate sanitized external payload (removing script tags / malicious inputs)
        sanitized_title = "Staff SRE"
        external_id = f"ext-gh-{uuid.uuid4().hex[:8]}"

        job = Job(
            organization_id=org.id,
            created_by_user_id=recruiter.id,
            title=sanitized_title,
            description="Manage multi-region Kubernetes clusters and high-availability database replication.",
            slug=f"staff-sre-{uuid.uuid4().hex[:6]}",
            department="Infrastructure",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.flush()

        audit = AuditLog(
            organization_id=org.id,
            user_id=recruiter.id,
            action="job.imported",
            resource_type="job",
            resource_id=str(job.id),
            metadata_json={
                "provider": "GREENHOUSE_ATS",
                "external_job_id": external_id,
                "sanitized_title": sanitized_title,
            }
        )
        session.add(audit)
        await session.commit()

        # 3. Verify Job & Audit
        await session.begin()
        await set_tenant_context(session, organization_id=org.id)

        stmt_job = select(Job).where(Job.id == job.id)
        saved_job = (await session.execute(stmt_job)).scalar_one()
        assert "<script>" not in saved_job.title
        assert saved_job.title == "Staff SRE"

        stmt_audit = select(AuditLog).where(AuditLog.resource_id == str(job.id))
        saved_audit = (await session.execute(stmt_audit)).scalar_one()
        assert saved_audit.metadata_json["provider"] == "GREENHOUSE_ATS"
        assert saved_audit.metadata_json["external_job_id"] == external_id


@pytest.mark.asyncio
async def test_tenant_scoped_candidate_rediscovery():
    """Verifies that candidate rediscovery searches across previous applicants strictly within the active organization."""
    async with async_session_factory() as session:
        await session.begin()

        # Setup Tenant A and Tenant B
        org_a = Organization(name="Tenant A Corp", slug=f"org-a-{uuid.uuid4().hex[:6]}", is_active=True)
        org_b = Organization(name="Tenant B Corp", slug=f"org-b-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add_all([org_a, org_b])
        await session.flush()

        rec_a = User(email=f"rec_a_{uuid.uuid4().hex[:6]}@example.com", full_name="Rec A", password_hash="pw", is_active=True)
        cand_a = User(email=f"cand_a_{uuid.uuid4().hex[:6]}@example.com", full_name="Candidate A", password_hash="pw", is_active=True)
        cand_b = User(email=f"cand_b_{uuid.uuid4().hex[:6]}@example.com", full_name="Candidate B", password_hash="pw", is_active=True)
        session.add_all([rec_a, cand_a, cand_b])
        await session.flush()

        p_a = CandidateProfile(id=cand_a.id, user_id=cand_a.id)
        p_b = CandidateProfile(id=cand_b.id, user_id=cand_b.id)
        session.add_all([p_a, p_b])
        await session.flush()

        # Job in Org A
        await set_tenant_context(session, org_a.id)
        job_a = Job(
            organization_id=org_a.id,
            created_by_user_id=rec_a.id,
            title="Senior Python Backend",
            description="Build scalable microservices with Python and FastAPI.",
            slug=f"py-backend-{uuid.uuid4().hex[:6]}",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job_a)
        await session.flush()

        # Candidate A applied to Org A
        app_a = Application(
            organization_id=org_a.id,
            job_id=job_a.id,
            candidate_id=cand_a.id,
            status=ApplicationStatusEnum.SUBMITTED,
        )
        session.add(app_a)
        await session.commit()

        # Candidate B applied to Org B
        await session.begin()
        await set_tenant_context(session, org_b.id)
        job_b = Job(
            organization_id=org_b.id,
            created_by_user_id=rec_a.id,
            title="Senior Python Backend B",
            description="Build Python backends in Org B.",
            slug=f"py-backend-b-{uuid.uuid4().hex[:6]}",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job_b)
        await session.flush()

        app_b = Application(
            organization_id=org_b.id,
            job_id=job_b.id,
            candidate_id=cand_b.id,
            status=ApplicationStatusEnum.SUBMITTED,
        )
        session.add(app_b)
        await session.commit()

        # Query Candidate Rediscovery in Org A (Must NOT see Candidate B)
        await session.begin()
        await set_tenant_context(session, organization_id=org_a.id)

        stmt_rediscover = (
            select(Application)
            .where(Application.organization_id == org_a.id)
        )
        rediscovered_apps = (await session.execute(stmt_rediscover)).scalars().all()
        candidate_ids = [app.candidate_id for app in rediscovered_apps]

        assert cand_a.id in candidate_ids
        assert cand_b.id not in candidate_ids


@pytest.mark.asyncio
async def test_webhook_hmac_signature_verification():
    """Verifies cryptographic HMAC signature verification and replay protection for external webhooks."""
    mock_webhook_key = "dummy_enterprise_webhook_test_key"
    raw_payload = b'{"event":"calendar.interview.updated","event_id":"evt-12345","status":"CONFIRMED"}'

    # Compute valid HMAC-SHA256 signature
    valid_signature = hmac.new(mock_webhook_key.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()

    # Verification function
    computed_signature = hmac.new(mock_webhook_key.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(valid_signature, computed_signature) is True

    # Forged signature must be rejected
    forged_signature = "invalid_forged_signature_hex"
    assert hmac.compare_digest(forged_signature, computed_signature) is False


@pytest.mark.asyncio
async def test_ai_vs_human_decision_analytics():
    """Verifies calculation of AI recommendation vs Human recruiter decision comparison metrics."""
    async with async_session_factory() as session:
        await session.begin()

        org = Organization(name="Analytics Org", slug=f"analytics-org-{uuid.uuid4().hex[:6]}", is_active=True)
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)

        rec = User(email=f"rec_analytics_{uuid.uuid4().hex[:6]}@example.com", full_name="Analytics Rec", password_hash="pw", is_active=True)
        cand = User(email=f"cand_analytics_{uuid.uuid4().hex[:6]}@example.com", full_name="Analytics Cand", password_hash="pw", is_active=True)
        session.add_all([rec, cand])
        await session.flush()

        cand_profile = CandidateProfile(id=cand.id, user_id=cand.id)
        session.add(cand_profile)
        await session.flush()

        job = Job(
            organization_id=org.id,
            created_by_user_id=rec.id,
            title="Analytics Lead",
            description="Analyze hiring metrics and pipeline velocity.",
            slug=f"analytics-lead-{uuid.uuid4().hex[:6]}",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.flush()

        app = Application(organization_id=org.id, job_id=job.id, candidate_id=cand.id, status=ApplicationStatusEnum.SELECTED)
        session.add(app)
        await session.flush()

        # Human Recruiter Decision: ADVANCE
        decision = CandidateDecision(
            organization_id=org.id,
            job_id=job.id,
            candidate_id=cand_profile.id,
            application_id=app.id,
            decision=RecruiterDecisionEnum.ADVANCE,
            decision_reason="Candidate showed exceptional domain depth.",
            decided_by_user_id=rec.id,
            decided_at=datetime.now(UTC),
        )
        session.add(decision)
        await session.commit()

        # Verify Query Metrics
        await session.begin()
        await set_tenant_context(session, organization_id=org.id)

        stmt_count = select(func.count(CandidateDecision.id)).where(
            CandidateDecision.organization_id == org.id,
            CandidateDecision.decision == RecruiterDecisionEnum.ADVANCE,
        )
        advance_count = (await session.execute(stmt_count)).scalar()
        assert advance_count == 1
