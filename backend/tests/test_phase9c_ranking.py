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
from app.domains.scoring.models import (
    EligibilityStatusEnum,
)
from app.infrastructure.embeddings.base import TestEmbeddingAdapter
from app.infrastructure.ranking.ranking_engine import RankingEngine
from app.main import app
from app.services.job_processor import JobProcessorService
from app.services.matching_service import MatchingService
from app.services.ranking_service import RankingService
from app.services.scoring_service import ScoringService

async def _setup_ranking_context(client: AsyncClient):
    rec_email = f"rec_p9c_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter Phase9C"})
    rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
    rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

    org_resp = await client.post("/api/v1/organizations", json={"name": "Phase9C Org", "slug": f"p9c-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    # Create Job Requisition
    job_resp = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Principal AI Architect",
            "description": "Must have 3+ years of Python experience. Experience with RAG is preferred.",
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

    # Helper to create and process candidate scoring
    async def create_candidate(name_suffix: str, exp_months: int, skills_list: list):
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, uuid.UUID(org_id))
            
            cand_user = User(
                email=f"cand_p9c_{name_suffix}_{uuid.uuid4().hex[:6]}@example.com",
                password_hash="hashed_pw_test",
                full_name=f"Candidate {name_suffix}",
            )
            session.add(cand_user)
            await session.flush()

            cand = CandidateProfile(
                user_id=cand_user.id,
                headline=f"AI Engineer {name_suffix}",
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
                file_name=f"resume_{name_suffix}.pdf",
                file_path=f"resumes/{cand.id}/resume.pdf",
                file_size_bytes=1024,
                extracted_text=f"{exp_months} months experience with {', '.join(skills_list)}.",
            )
            session.add(doc)
            await session.flush()

            for sk in skills_list:
                c_skill = CandidateSkill(
                    organization_id=uuid.UUID(org_id),
                    candidate_id=cand_user.id,
                    document_id=doc.id,
                    raw_skill_name=sk,
                    canonical_skill_name=sk,
                )
                session.add(c_skill)

            c_exp = CandidateExperience(
                organization_id=uuid.UUID(org_id),
                candidate_id=cand_user.id,
                document_id=doc.id,
                company_name="TechCorp",
                job_title="Engineer",
                duration_months=exp_months,
            )
            session.add(c_exp)

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
            app_id = app_rec.id

        # Phase 9A Matching & Phase 9B Scoring
        m_service = MatchingService()
        await m_service.process_candidate_matching(job_id=uuid.UUID(job_id), candidate_id=cand_id, organization_id=uuid.UUID(org_id))

        s_service = ScoringService()
        await s_service.process_candidate_scoring(job_id=uuid.UUID(job_id), candidate_id=cand_id, organization_id=uuid.UUID(org_id), application_id=app_id)

        return {"cand_id": cand_id, "app_id": app_id}

    candA = await create_candidate("A", 60, ["Python", "RAG"])
    candB = await create_candidate("B", 48, ["Python"])
    candC = await create_candidate("C", 36, ["Python"])

    return {
        "org_id": uuid.UUID(org_id),
        "job_id": uuid.UUID(job_id),
        "candA": candA,
        "candB": candB,
        "candC": candC,
        "rec_headers": rec_headers,
    }

@pytest.mark.asyncio
async def test_deterministic_ranking_ordering():
    cands = [
        {"candidate_id": uuid.UUID("00000000-0000-0000-0000-000000000003"), "score": 80.0, "eligibility_status": EligibilityStatusEnum.PASS, "score_confidence": 0.90},
        {"candidate_id": uuid.UUID("00000000-0000-0000-0000-000000000001"), "score": 95.0, "eligibility_status": EligibilityStatusEnum.PASS, "score_confidence": 0.95},
        {"candidate_id": uuid.UUID("00000000-0000-0000-0000-000000000002"), "score": 90.0, "eligibility_status": EligibilityStatusEnum.PASS, "score_confidence": 0.92},
    ]
    
    ranked = RankingEngine.rank_candidates(cands, top_k=2)
    assert ranked[0]["candidate_id"] == uuid.UUID("00000000-0000-0000-0000-000000000001")
    assert ranked[0]["rank_position"] == 1
    assert ranked[0]["is_top_k"] is True

    assert ranked[1]["candidate_id"] == uuid.UUID("00000000-0000-0000-0000-000000000002")
    assert ranked[1]["rank_position"] == 2
    assert ranked[1]["is_top_k"] is True

    assert ranked[2]["candidate_id"] == uuid.UUID("00000000-0000-0000-0000-000000000003")
    assert ranked[2]["rank_position"] == 3
    assert ranked[2]["is_top_k"] is False

@pytest.mark.asyncio
async def test_top_k_selection_and_boundaries():
    cands = [
        {"candidate_id": uuid.uuid4(), "score": 90.0, "eligibility_status": EligibilityStatusEnum.PASS},
        {"candidate_id": uuid.uuid4(), "score": 80.0, "eligibility_status": EligibilityStatusEnum.PASS},
    ]

    # K = 1
    ranked1 = RankingEngine.rank_candidates(cands, top_k=1)
    assert ranked1[0]["is_top_k"] is True
    assert ranked1[1]["is_top_k"] is False

    # K = 5 (K > candidate_count)
    ranked5 = RankingEngine.rank_candidates(cands, top_k=5)
    assert ranked5[0]["is_top_k"] is True
    assert ranked5[1]["is_top_k"] is True

@pytest.mark.asyncio
async def test_hard_requirement_failure_ineligible_ranking():
    cands = [
        {"candidate_id": uuid.UUID("00000000-0000-0000-0000-000000000001"), "score": 99.0, "eligibility_status": EligibilityStatusEnum.FAIL},
        {"candidate_id": uuid.UUID("00000000-0000-0000-0000-000000000002"), "score": 85.0, "eligibility_status": EligibilityStatusEnum.PASS},
    ]

    ranked = RankingEngine.rank_candidates(cands, top_k=5)
    
    # Eligible candidate (score 85) MUST outrank ineligible candidate (score 99)
    assert ranked[0]["candidate_id"] == uuid.UUID("00000000-0000-0000-0000-000000000002")
    assert ranked[0]["rank_position"] == 1
    assert ranked[0]["is_top_k"] is True

    assert ranked[1]["candidate_id"] == uuid.UUID("00000000-0000-0000-0000-000000000001")
    assert ranked[1]["rank_position"] == 2
    assert ranked[1]["is_top_k"] is False  # Ineligible candidate can NEVER consume a Top-K slot

@pytest.mark.asyncio
async def test_deterministic_tie_breaking():
    id_a = uuid.UUID("00000000-0000-0000-0000-000000000001")
    id_b = uuid.UUID("00000000-0000-0000-0000-000000000002")

    # Identical score (90.0) and confidence (0.90)
    cands = [
        {"candidate_id": id_b, "score": 90.0, "score_confidence": 0.90, "eligibility_status": EligibilityStatusEnum.PASS, "failed_hard_reqs_count": 0, "matched_reqs_count": 2},
        {"candidate_id": id_a, "score": 90.0, "score_confidence": 0.90, "eligibility_status": EligibilityStatusEnum.PASS, "failed_hard_reqs_count": 0, "matched_reqs_count": 2},
    ]

    ranked = RankingEngine.rank_candidates(cands, top_k=10)
    
    # Candidate ID ASC tie-breaker guarantees candidate id_a ranks before id_b
    assert ranked[0]["candidate_id"] == id_a
    assert ranked[1]["candidate_id"] == id_b

@pytest.mark.asyncio
async def test_ranking_service_end_to_end():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_ranking_context(client)

        r_service = RankingService()

        # Generate Ranking Snapshot
        ranking_v = await r_service.generate_ranking_snapshot(
            job_id=data["job_id"],
            organization_id=data["org_id"],
            top_k=2,
        )
        assert ranking_v is not None
        assert ranking_v.candidate_count == 3
        assert ranking_v.eligible_candidate_count == 3

        # API Retrieval
        res = await client.get(
            f"/api/v1/jobs/{data['job_id']}/ranking",
            headers=data["rec_headers"],
        )
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 3
        assert len(body["items"]) == 3
        assert body["items"][0]["rank_position"] == 1
        assert body["items"][0]["is_top_k"] is True
        assert body["items"][1]["rank_position"] == 2
        assert body["items"][1]["is_top_k"] is True
        assert body["items"][2]["rank_position"] == 3
        assert body["items"][2]["is_top_k"] is False

@pytest.mark.asyncio
async def test_ranking_reproducibility():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_ranking_context(client)

        r_service = RankingService()
        v1 = await r_service.generate_ranking_snapshot(job_id=data["job_id"], organization_id=data["org_id"], top_k=5)
        v2 = await r_service.generate_ranking_snapshot(job_id=data["job_id"], organization_id=data["org_id"], top_k=5)

        res1 = await client.get(f"/api/v1/jobs/{data['job_id']}/ranking?version_number={v1.ranking_version}", headers=data["rec_headers"])
        res2 = await client.get(f"/api/v1/jobs/{data['job_id']}/ranking?version_number={v2.ranking_version}", headers=data["rec_headers"])

        items1 = res1.json()["items"]
        items2 = res2.json()["items"]

        assert len(items1) == len(items2)
        for i in range(len(items1)):
            assert items1[i]["candidate_id"] == items2[i]["candidate_id"]
            assert items1[i]["rank_position"] == items2[i]["rank_position"]
            assert items1[i]["score"] == items2[i]["score"]

@pytest.mark.asyncio
async def test_stale_job_intelligence_guard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_ranking_context(client)

        # Transition Job Intelligence to STALE
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, data["org_id"])
            stmt = select(JobIntelligenceVersion).where(
                JobIntelligenceVersion.job_id == data["job_id"],
                JobIntelligenceVersion.organization_id == data["org_id"],
            )
            j_intel = (await session.execute(stmt)).scalars().first()
            j_intel.status = JobIntelligenceVersionStatusEnum.STALE
            await session.commit()

        r_service = RankingService()
        ranking_v = await r_service.generate_ranking_snapshot(job_id=data["job_id"], organization_id=data["org_id"])
        
        # Guard MUST prevent ranking generation against STALE job intelligence
        assert ranking_v is None

@pytest.mark.asyncio
async def test_negative_governance_no_llm_or_application_mutation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_ranking_context(client)

        r_service = RankingService()
        await r_service.generate_ranking_snapshot(job_id=data["job_id"], organization_id=data["org_id"])

        # Verify Application.status is NOT mutated by ranking generation
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, data["org_id"])
            stmt = select(Application).where(Application.id == data["candA"]["app_id"])
            app_obj = (await session.execute(stmt)).scalar_one()
            
            # Application status MUST remain SUBMITTED; ranking MUST NOT mutate status
            assert app_obj.status == ApplicationStatusEnum.SUBMITTED

@pytest.mark.asyncio
async def test_ranking_tenant_rls_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data_org1 = await _setup_ranking_context(client)
        data_org2 = await _setup_ranking_context(client)

        r_service = RankingService()
        await r_service.generate_ranking_snapshot(job_id=data_org1["job_id"], organization_id=data_org1["org_id"])

        # Org 2 Recruiter attempting to query Org 1 rankings -> Denied (HTTP 404 via RLS)
        res = await client.get(
            f"/api/v1/jobs/{data_org1['job_id']}/ranking",
            headers=data_org2["rec_headers"],
        )
        assert res.status_code == 404
