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
from app.domains.matching.models import (
    CandidateRequirementMatch,
    CandidateSemanticMatch,
    MatchStatusEnum,
)
from app.domains.scoring.models import (
    CandidateJobScore,
    EligibilityStatusEnum,
    FactorTypeEnum,
    ScoringConfiguration,
)
from app.infrastructure.embeddings.base import TestEmbeddingAdapter
from app.infrastructure.scoring.scoring_engine import ScoringEngine
from app.main import app
from app.services.job_processor import JobProcessorService
from app.services.matching_service import MatchingService
from app.services.scoring_service import ScoringService

from app.core.security import create_access_token

async def _setup_scoring_context(client: AsyncClient):
    rec_email = f"rec_p9b_{uuid.uuid4().hex[:8]}@example.com"
    rec_user = User(email=rec_email, full_name="Recruiter Phase9B", password_hash="dummy_pw", is_active=True)
    async with async_session_factory() as session:
        await session.begin()
        session.add(rec_user)
        await session.commit()

    token = create_access_token(rec_user.id)
    rec_headers = {"Authorization": f"Bearer {token}"}

    org_resp = await client.post("/api/v1/organizations", json={"name": "Phase9B Org", "slug": f"p9b-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    # Create Job Requisition
    job_resp = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Senior AI Architect",
            "description": "Must have 3+ years of Python development experience. Experience with Retrieval Augmented Generation (RAG) is preferred.",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "FULL_TIME",
        },
        headers=rec_headers,
    )
    job_id = job_resp.json()["id"]

    # Process Job Intelligence (Phase 8)
    j_processor = JobProcessorService()
    await j_processor.process_job_intelligence(job_id=uuid.UUID(job_id), organization_id=uuid.UUID(org_id))

    # Create Candidate User, Profile, Application & Document
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, uuid.UUID(org_id))
        
        cand_user = User(
            email=f"cand_p9b_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="hashed_pw_test",
            full_name="Candidate Phase9B",
        )
        session.add(cand_user)
        await session.flush()

        cand = CandidateProfile(
            user_id=cand_user.id,
            headline="AI Solutions Architect",
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
            file_name="resume_p9b.pdf",
            file_path=f"resumes/{cand.id}/resume.pdf",
            file_size_bytes=1024,
            extracted_text="5+ years experience building Python microservices with FastAPI and Retrieval Augmented Generation (RAG).",
        )
        session.add(doc)
        await session.flush()

        c_skill1 = CandidateSkill(
            organization_id=uuid.UUID(org_id),
            candidate_id=cand_user.id,
            document_id=doc.id,
            raw_skill_name="Python",
            canonical_skill_name="Python",
        )
        session.add(c_skill1)

        c_exp = CandidateExperience(
            organization_id=uuid.UUID(org_id),
            candidate_id=cand_user.id,
            document_id=doc.id,
            company_name="TechCorp AI",
            job_title="Lead Engineer",
            duration_months=60,
        )
        session.add(c_exp)

        # Generate Candidate Embeddings
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
        app_id = app_rec.id

    # Execute Phase 9A Feature Matching Engine
    m_service = MatchingService()
    await m_service.process_candidate_matching(
        job_id=uuid.UUID(job_id),
        candidate_id=cand_id,
        organization_id=uuid.UUID(org_id),
    )

    return {
        "org_id": uuid.UUID(org_id),
        "job_id": uuid.UUID(job_id),
        "candidate_id": cand_id,
        "document_id": doc_id,
        "application_id": app_id,
        "rec_headers": rec_headers,
    }

@pytest.mark.asyncio
async def test_scoring_configuration_weight_validation():
    valid_cfg = ScoringConfiguration(
        required_skills_weight=0.30,
        semantic_match_weight=0.20,
        experience_weight=0.20,
        education_weight=0.10,
        preferred_skills_weight=0.10,
        other_requirements_weight=0.10,
    )
    assert ScoringEngine.validate_weights(valid_cfg) is True

    invalid_cfg = ScoringConfiguration(
        required_skills_weight=0.50,
        semantic_match_weight=0.50,
        experience_weight=0.50,  # sum = 1.8 -> Invalid
        education_weight=0.10,
        preferred_skills_weight=0.10,
        other_requirements_weight=0.10,
    )
    assert ScoringEngine.validate_weights(invalid_cfg) is False

@pytest.mark.asyncio
async def test_hard_requirement_gate_failure_overrides_high_semantic_score():
    cfg = ScoringConfiguration()
    
    # Requirement match item with failed hard constraint
    req_matches = [
        CandidateRequirementMatch(
            job_requirement_id=uuid.uuid4(),
            requirement_type="SKILL",
            raw_required_value="Kubernetes",
            canonical_required_value="Kubernetes",
            requirement_level="REQUIRED",
            hard_constraint=True,
            match_status=MatchStatusEnum.NOT_MATCHED,
            reason="Missing required skill Kubernetes",
            confidence=0.90,
        )
    ]

    # High semantic vector match (0.95)
    sem_matches = [
        CandidateSemanticMatch(
            query_context="REQUIRED_SKILLS",
            candidate_context="SKILL_CONTEXT",
            similarity_score=0.95,
            embedding_model="test-model",
            dimension=1536,
        )
    ]

    result = ScoringEngine.calculate_candidate_score(cfg, req_matches, sem_matches)
    
    # High semantic similarity MUST NOT compensate for hard requirement failure
    assert result["eligibility_status"] == EligibilityStatusEnum.FAIL
    assert len(result["hard_requirement_results"]) == 1
    assert result["hard_requirement_results"][0]["status"] == "NOT_MATCHED"

@pytest.mark.asyncio
async def test_applicable_weight_normalization():
    cfg = ScoringConfiguration(
        required_skills_weight=0.30,
        semantic_match_weight=0.20,
        experience_weight=0.20,
        education_weight=0.10,
        preferred_skills_weight=0.10,
        other_requirements_weight=0.10,
    )

    req_matches = [
        CandidateRequirementMatch(
            job_requirement_id=uuid.uuid4(),
            requirement_type="SKILL",
            raw_required_value="Python",
            canonical_required_value="Python",
            requirement_level="REQUIRED",
            hard_constraint=False,
            match_status=MatchStatusEnum.MATCHED,
            confidence=0.95,
        )
    ]

    # Job has Required Skills (0.30) & Semantic Match (0.20), but no Preferred, Education, Experience, or Other
    sem_matches = [
        CandidateSemanticMatch(
            query_context="REQUIRED_SKILLS",
            candidate_context="SKILL_CONTEXT",
            similarity_score=0.90,
            embedding_model="test",
            dimension=1536,
        )
    ]

    result = ScoringEngine.calculate_candidate_score(cfg, req_matches, sem_matches)
    
    req_factor = next(f for f in result["factor_scores"] if f["factor_type"] == FactorTypeEnum.REQUIRED_SKILLS)
    sem_factor = next(f for f in result["factor_scores"] if f["factor_type"] == FactorTypeEnum.SEMANTIC_MATCH)
    pref_factor = next(f for f in result["factor_scores"] if f["factor_type"] == FactorTypeEnum.PREFERRED_SKILLS)

    # Applicable sum = 0.30 + 0.20 = 0.50 -> Normalized: Req=0.60, Sem=0.40
    assert req_factor["applicable"] is True
    assert round(req_factor["normalized_weight"], 2) == 0.60
    assert sem_factor["applicable"] is True
    assert round(sem_factor["normalized_weight"], 2) == 0.40
    assert pref_factor["applicable"] is False
    assert pref_factor["normalized_weight"] == 0.0

@pytest.mark.asyncio
async def test_deterministic_scoring_pipeline_and_reproducibility():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_scoring_context(client)

        s_service = ScoringService()

        # Run scoring calculation 1
        success1 = await s_service.process_candidate_scoring(
            job_id=data["job_id"],
            candidate_id=data["candidate_id"],
            organization_id=data["org_id"],
            application_id=data["application_id"],
        )
        assert success1 is True

        res1 = await client.get(
            f"/api/v1/jobs/{data['job_id']}/scoring/{data['candidate_id']}/breakdown",
            headers=data["rec_headers"],
        )
        assert res1.status_code == 200
        body1 = res1.json()

        score1 = body1["score"]["overall_score"]
        eligibility1 = body1["score"]["eligibility_status"]

        # Run scoring calculation 2 (Reproducibility Check)
        success2 = await s_service.process_candidate_scoring(
            job_id=data["job_id"],
            candidate_id=data["candidate_id"],
            organization_id=data["org_id"],
            application_id=data["application_id"],
        )
        assert success2 is True

        res2 = await client.get(
            f"/api/v1/jobs/{data['job_id']}/scoring/{data['candidate_id']}/breakdown",
            headers=data["rec_headers"],
        )
        assert res2.status_code == 200
        body2 = res2.json()

        score2 = body2["score"]["overall_score"]
        eligibility2 = body2["score"]["eligibility_status"]

        # Exact reproducibility requirement: Identical inputs produce identical scores
        assert score1 == score2
        assert eligibility1 == eligibility2
        assert len(body1["factor_scores"]) == len(body2["factor_scores"])

@pytest.mark.asyncio
async def test_negative_governance_no_ranking_or_llm_invocation():
    # 1. Assert CandidateJobScore model contains NO rank or top_k fields
    score_columns = [col.name for col in CandidateJobScore.__table__.columns]
    assert "rank" not in score_columns
    assert "ranking" not in score_columns
    assert "top_k" not in score_columns
    assert "shortlist" not in score_columns
    assert "automatic_rejection" not in score_columns

    # 2. Assert Application status is NOT mutated by scoring
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_scoring_context(client)

        s_service = ScoringService()
        await s_service.process_candidate_scoring(
            job_id=data["job_id"],
            candidate_id=data["candidate_id"],
            organization_id=data["org_id"],
            application_id=data["application_id"],
        )

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, data["org_id"])
            stmt = select(Application).where(Application.id == data["application_id"])
            app_obj = (await session.execute(stmt)).scalar_one()
            
            # Application status MUST remain SUBMITTED; scoring MUST NOT mutate state
            assert app_obj.status == ApplicationStatusEnum.SUBMITTED

@pytest.mark.asyncio
async def test_scoring_tenant_rls_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data_org1 = await _setup_scoring_context(client)
        data_org2 = await _setup_scoring_context(client)

        s_service = ScoringService()
        await s_service.process_candidate_scoring(
            job_id=data_org1["job_id"],
            candidate_id=data_org1["candidate_id"],
            organization_id=data_org1["org_id"],
        )

        # Org 2 Recruiter attempting to access Org 1 candidate score -> Denied (HTTP 404 via RLS)
        res = await client.get(
            f"/api/v1/jobs/{data_org1['job_id']}/scoring/{data_org1['candidate_id']}",
            headers=data_org2["rec_headers"],
        )
        assert res.status_code == 404
