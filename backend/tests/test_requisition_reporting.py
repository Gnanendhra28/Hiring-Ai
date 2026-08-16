import uuid
import pytest
from sqlalchemy import text
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory, engine
from app.domains.applications.models import Application, ApplicationStatusEnum, CandidatePlacement, OfferStatusEnum
from app.domains.candidates.models import CandidateProfile
from app.domains.document_intelligence.models import CandidateDocument, DocumentProcessingStatusEnum
from app.domains.identity.models import User
from app.domains.job_intelligence.models import JobIntelligenceVersion, JobIntelligenceVersionStatusEnum
from app.domains.jobs.models import Job, JobStatusEnum
from app.domains.organizations.models import Organization
from app.domains.scoring.models import CandidateJobScore, ScoringConfiguration
from app.services.requisition_reporting_service import RequisitionReportingService

async def ensure_tables():
    async with engine.begin() as conn:
        await conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'offerstatusenum') THEN CREATE TYPE offerstatusenum AS ENUM ('NOT_CREATED', 'OFFER_EXTENDED', 'OFFER_ACCEPTED', 'OFFER_REJECTED', 'HIRED'); END IF; END $$;"))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS candidate_placements (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                candidate_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                application_id UUID NOT NULL UNIQUE REFERENCES applications(id) ON DELETE CASCADE,
                offer_status offerstatusenum NOT NULL DEFAULT 'NOT_CREATED',
                offer_created_at TIMESTAMPTZ,
                offer_accepted_at TIMESTAMPTZ,
                placed_at TIMESTAMPTZ,
                created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                notes TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

@pytest.mark.asyncio
async def test_requisition_reporting_service_basic():
    await ensure_tables()
    service = RequisitionReportingService()
    org_id = uuid.uuid4()
    candidate_id = uuid.uuid4()

    async with async_session_factory() as session:
        await session.begin()
        
        org = Organization(id=org_id, name="Test Org", slug=f"test-org-{org_id}")
        session.add(org)

        usr = User(id=candidate_id, email=f"candidate_{candidate_id}@example.com", password_hash="hash", full_name="Candidate Name")
        session.add(usr)
        await session.flush()

        cp = CandidateProfile(id=candidate_id, user_id=candidate_id)
        session.add(cp)
        await session.flush()

        await set_tenant_context(session, organization_id=org_id)

        job = Job(
            id=uuid.uuid4(),
            organization_id=org_id,
            title="Senior AI Engineer",
            slug="senior-ai-engineer",
            description="Build LLM & RLS backend pipelines",
            status=JobStatusEnum.PUBLISHED,
        )
        session.add(job)
        await session.flush()

        intel_v = JobIntelligenceVersion(
            id=uuid.uuid4(),
            organization_id=org_id,
            job_id=job.id,
            version_number=1,
            is_active=True,
            status=JobIntelligenceVersionStatusEnum.COMPLETED,
        )
        session.add(intel_v)

        scoring_cfg = ScoringConfiguration(
            id=uuid.uuid4(),
            organization_id=org_id,
            version_number=1,
            is_active=True,
        )
        session.add(scoring_cfg)

        app_obj = Application(
            id=uuid.uuid4(),
            organization_id=org_id,
            job_id=job.id,
            candidate_id=candidate_id,
            status=ApplicationStatusEnum.SUBMITTED,
        )
        session.add(app_obj)
        await session.flush()

        cand_doc = CandidateDocument(
            id=uuid.uuid4(),
            organization_id=org_id,
            candidate_id=candidate_id,
            application_id=app_obj.id,
            file_name="resume.pdf",
            file_path="resumes/resume.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
        )
        session.add(cand_doc)
        await session.flush()

        score_obj = CandidateJobScore(
            id=uuid.uuid4(),
            organization_id=org_id,
            job_id=job.id,
            job_intelligence_version_id=intel_v.id,
            candidate_id=candidate_id,
            candidate_document_id=cand_doc.id,
            application_id=app_obj.id,
            scoring_configuration_id=scoring_cfg.id,
            overall_score=88.5,
            eligibility_status="PASS",
            confidence_tier="HIGH",
        )
        session.add(score_obj)

        await session.commit()

        report = await service.get_requisition_report(job_id=job.id, organization_id=org_id)
        assert report is not None
        assert report.requisition_id == job.id
        assert report.organization_id == org_id
        assert report.title == "Senior AI Engineer"
        assert report.total_applications == 1
        assert report.eligible_applications == 1
        assert report.score_analytics.average_score == 88.5
        assert report.score_analytics.confidence_distribution["HIGH"] == 1

@pytest.mark.asyncio
async def test_requisition_reporting_tenant_isolation():
    await ensure_tables()
    service = RequisitionReportingService()
    org_id_1 = uuid.uuid4()
    org_id_2 = uuid.uuid4()

    async with async_session_factory() as session:
        await session.begin()

        org1 = Organization(id=org_id_1, name="Org 1", slug=f"org-1-{org_id_1}")
        org2 = Organization(id=org_id_2, name="Org 2", slug=f"org-2-{org_id_2}")
        session.add_all([org1, org2])
        await session.flush()

        await set_tenant_context(session, organization_id=org_id_1)

        job = Job(
            id=uuid.uuid4(),
            organization_id=org_id_1,
            title="Frontend Specialist",
            slug="frontend-specialist",
            description="React & Next.js App Router",
            status=JobStatusEnum.PUBLISHED,
        )
        session.add(job)
        await session.commit()

        # Access with wrong org_id should return None (Tenant Guard / RLS Isolation)
        report_cross = await service.get_requisition_report(job_id=job.id, organization_id=org_id_2)
        assert report_cross is None

@pytest.mark.asyncio
async def test_requisition_reporting_csv_export():
    await ensure_tables()
    service = RequisitionReportingService()
    org_id = uuid.uuid4()

    async with async_session_factory() as session:
        await session.begin()

        org = Organization(id=org_id, name="Org CSV", slug=f"org-csv-{org_id}")
        session.add(org)
        await session.flush()

        await set_tenant_context(session, organization_id=org_id)

        job = Job(
            id=uuid.uuid4(),
            organization_id=org_id,
            title="ML Operations Lead",
            slug="mlops-lead",
            description="Manage ML pipelines & pgvector",
            status=JobStatusEnum.PUBLISHED,
        )
        session.add(job)
        await session.commit()

        csv_data = await service.export_requisition_report_csv(job_id=job.id, organization_id=org_id)
        assert csv_data is not None
        assert "Metric Category,Metric Name,Value" in csv_data
        assert "ML Operations Lead" in csv_data
        assert "Requisition Overview,Title,ML Operations Lead" in csv_data
