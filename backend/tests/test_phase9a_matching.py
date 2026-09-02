import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.candidates.models import CandidateProfile
from app.domains.document_intelligence.models import (
    CandidateDocument,
    CandidateEmbedding,
    CandidateSkill,
    CandidateExperience,
)
from app.domains.identity.models import User
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
)
from app.domains.matching.models import (
    MatchStatusEnum,
)
from app.infrastructure.embeddings.base import TestEmbeddingAdapter
from app.infrastructure.matching.hard_rule_engine import HardRequirementEngine
from app.infrastructure.matching.skill_matcher import SkillMatcher
from app.main import app
from app.services.job_processor import JobProcessorService
from app.services.matching_service import MatchingService

from app.core.security import create_access_token

async def _setup_matching_context(client: AsyncClient):
    rec_email = f"rec_p9a_{uuid.uuid4().hex[:8]}@example.com"
    rec_user = User(email=rec_email, full_name="Recruiter Phase9A", password_hash="dummy_pw", is_active=True)
    async with async_session_factory() as session:
        await session.begin()
        session.add(rec_user)
        await session.commit()

    token = create_access_token(rec_user.id)
    rec_headers = {"Authorization": f"Bearer {token}"}

    org_resp = await client.post("/api/v1/organizations", json={"name": "Phase9A Org", "slug": f"p9a-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    # Create Job
    job_resp = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Lead Python RAG Architect",
            "description": "Must have 3+ years of Python development experience. Experience with Retrieval Augmented Generation (RAG) is preferred.",
            "department": "AI Engineering",
            "location": "Austin, TX",
            "employment_type": "FULL_TIME",
        },
        headers=rec_headers,
    )
    job_id = job_resp.json()["id"]

    # Process Job Intelligence
    j_processor = JobProcessorService()
    await j_processor.process_job_intelligence(job_id=uuid.UUID(job_id), organization_id=uuid.UUID(org_id))

    # Create Candidate User & Candidate Profile & Application & Document
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, uuid.UUID(org_id))

        cand_user = User(
            email=f"cand_p9a_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_pw_test",
            full_name="Candidate Phase9A",
        )
        session.add(cand_user)
        await session.flush()

        cand = CandidateProfile(
            user_id=cand_user.id,
            headline="AI Engineer",
        )
        session.add(cand)
        await session.flush()

        app_rec = Application(
            organization_id=uuid.UUID(org_id),
            job_id=uuid.UUID(job_id),
            candidate_id=cand_user.id,
            status=ApplicationStatusEnum.SUBMITTED,
        )
        session.add(app_rec)
        await session.flush()

        doc = CandidateDocument(
            organization_id=uuid.UUID(org_id),
            application_id=app_rec.id,
            candidate_id=cand_user.id,
            file_name="resume_p9a.pdf",
            file_path=f"resumes/{cand.id}/resume.pdf",
            file_size_bytes=1024,
            extracted_text="5+ years experience building Python microservices with FastAPI and Retrieval Augmented Generation (RAG).",
        )
        session.add(doc)
        await session.flush()

        c_skill = CandidateSkill(
            organization_id=uuid.UUID(org_id),
            candidate_id=cand_user.id,
            document_id=doc.id,
            raw_skill_name="Python",
            canonical_skill_name="Python",
        )
        session.add(c_skill)

        c_exp = CandidateExperience(
            organization_id=uuid.UUID(org_id),
            candidate_id=cand_user.id,
            document_id=doc.id,
            company_name="Acme AI Corp",
            job_title="Senior AI Engineer",
            duration_months=48,
        )
        session.add(c_exp)

        # Generate test Candidate Embeddings
        emb_adapter = TestEmbeddingAdapter()
        for ctx_type in ["SKILL_CONTEXT", "EXPERIENCE_CONTEXT", "SUMMARY"]:
            vec = await emb_adapter.generate_embedding(doc.extracted_text)
            c_emb = CandidateEmbedding(
                organization_id=uuid.UUID(org_id),
                candidate_id=cand_user.id,
                document_id=doc.id,
                context_type=ctx_type,
                embedding=vec,
                provider="TEST",
                model_name="test-embedding",
                dimension=1536,
            )
            session.add(c_emb)

        await session.commit()

        cand_id = cand.id
        doc_id = doc.id

    return {
        "org_id": uuid.UUID(org_id),
        "job_id": uuid.UUID(job_id),
        "candidate_id": cand_id,
        "document_id": doc_id,
        "rec_headers": rec_headers,
    }

@pytest.mark.asyncio
async def test_hard_requirement_engine_experience_operators():
    res_gte, msg1 = HardRequirementEngine.evaluate_experience("GTE", 36.0, None, 48.0)
    assert res_gte == MatchStatusEnum.MATCHED

    res_fail, msg2 = HardRequirementEngine.evaluate_experience("GTE", 36.0, None, 24.0)
    assert res_fail == MatchStatusEnum.NOT_MATCHED

    res_unk, msg3 = HardRequirementEngine.evaluate_experience("GTE", 36.0, None, None)
    assert res_unk == MatchStatusEnum.UNKNOWN

@pytest.mark.asyncio
async def test_skill_matching_and_evidence_verification():
    status, conf, reason, quote, v_status = SkillMatcher.match_skill(
        raw_required_skill="Retrieval Augmented Generation",
        canonical_required_skill="RAG",
        candidate_skills=[{"skill_name": "RAG"}],
        candidate_resume_text="Built Retrieval Augmented Generation (RAG) microservices.",
        is_protected_feature=False,
    )
    assert status == MatchStatusEnum.MATCHED
    assert conf >= 0.85
    assert v_status == "VERIFIED"

@pytest.mark.asyncio
async def test_protected_feature_exclusion():
    status, conf, reason, quote, v_status = SkillMatcher.match_skill(
        raw_required_skill="Young male candidate",
        canonical_required_skill="Young Male",
        candidate_skills=[],
        candidate_resume_text="",
        is_protected_feature=True,
    )
    assert status == MatchStatusEnum.PROTECTED_EXCLUDED

@pytest.mark.asyncio
async def test_candidate_matching_service_pipeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_matching_context(client)

        m_service = MatchingService()
        success = await m_service.process_candidate_matching(
            job_id=data["job_id"],
            candidate_id=data["candidate_id"],
            organization_id=data["org_id"],
        )
        assert success is True

        # Fetch candidate feature match details via API
        res = await client.get(
            f"/api/v1/jobs/{data['job_id']}/matching/features/{data['candidate_id']}",
            headers=data["rec_headers"],
        )
        assert res.status_code == 200
        body = res.json()

        assert body["match"]["status"] == "COMPLETED"
        assert len(body["requirement_matches"]) > 0
        assert len(body["semantic_matches"]) > 0

@pytest.mark.asyncio
async def test_matching_stale_job_intelligence_guard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_matching_context(client)

        # Mark active Job Intelligence STALE
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, data["org_id"])
            stmt_v = select(JobIntelligenceVersion).where(JobIntelligenceVersion.job_id == data["job_id"])
            v = (await session.execute(stmt_v)).scalars().first()
            v.status = JobIntelligenceVersionStatusEnum.STALE
            await session.commit()

        # Attempt candidate matching -> Fails due to STALE intelligence guard
        m_service = MatchingService()
        success = await m_service.process_candidate_matching(
            job_id=data["job_id"],
            candidate_id=data["candidate_id"],
            organization_id=data["org_id"],
        )
        assert success is False

@pytest.mark.asyncio
async def test_matching_tenant_rls_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data_org1 = await _setup_matching_context(client)
        data_org2 = await _setup_matching_context(client)

        m_service = MatchingService()
        await m_service.process_candidate_matching(
            job_id=data_org1["job_id"],
            candidate_id=data_org1["candidate_id"],
            organization_id=data_org1["org_id"],
        )

        # Org 2 Recruiter attempting to query Org 1 match features -> Denied (404)
        res = await client.get(
            f"/api/v1/jobs/{data_org1['job_id']}/matching/features/{data_org1['candidate_id']}",
            headers=data_org2["rec_headers"],
        )
        assert res.status_code == 404
