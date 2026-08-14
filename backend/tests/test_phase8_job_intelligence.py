import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select

from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
)
from app.infrastructure.parsing.job_parser import DeterministicJobParser
from app.infrastructure.safety.protected_feature_filter import ProtectedFeatureFilter
from app.infrastructure.skills.normalizer import SkillNormalizer
from app.main import app
from app.services.job_processor import JobProcessorService

async def _setup_job_intelligence_context(client: AsyncClient):
    rec_email = f"rec_p8_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter Phase8"})
    rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
    rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

    org_resp = await client.post("/api/v1/organizations", json={"name": "Phase8 Org", "slug": f"p8-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    job_resp = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Lead Python RAG Architect",
            "description": "Must have 3+ years of Python development experience. Experience with Retrieval Augmented Generation (RAG) is preferred. Hybrid working 3 days in office.",
            "department": "AI Engineering",
            "location": "Austin, TX",
            "employment_type": "FULL_TIME",
        },
        headers=rec_headers,
    )
    job_id = job_resp.json()["id"]

    return {
        "org_id": uuid.UUID(org_id),
        "job_id": uuid.UUID(job_id),
        "rec_headers": rec_headers,
    }

@pytest.mark.asyncio
async def test_job_intelligence_version_creation_and_activation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_job_intelligence_context(client)

        processor = JobProcessorService()
        success = await processor.process_job_intelligence(
            job_id=data["job_id"],
            organization_id=data["org_id"],
        )
        assert success is True

        # Fetch Active Intelligence
        intel_res = await client.get(f"/api/v1/jobs/{data['job_id']}/intelligence", headers=data["rec_headers"])
        assert intel_res.status_code == 200
        body = intel_res.json()

        assert body["version"]["version_number"] == 1
        assert body["version"]["is_active"] is True
        assert body["version"]["status"] == "COMPLETED"
        assert len(body["requirements"]) > 0

@pytest.mark.asyncio
async def test_job_edit_transitions_intelligence_to_stale():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_job_intelligence_context(client)

        processor = JobProcessorService()
        await processor.process_job_intelligence(job_id=data["job_id"], organization_id=data["org_id"])

        # Edit Job Requisition
        update_res = await client.put(
            f"/api/v1/jobs/{data['job_id']}",
            json={
                "title": "Senior Python RAG Architect (Updated)",
                "description": "Must have 5+ years of Python development experience.",
                "department": "AI Engineering",
                "location": "Austin, TX",
                "employment_type": "FULL_TIME",
            },
            headers=data["rec_headers"],
        )
        assert update_res.status_code == 200

        # Verify Intelligence Version status is STALE within RLS tenant context
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, data["org_id"])
            stmt_v = select(JobIntelligenceVersion).where(JobIntelligenceVersion.job_id == data["job_id"])
            v = (await session.execute(stmt_v)).scalars().first()
            assert v.status == JobIntelligenceVersionStatusEnum.STALE

@pytest.mark.asyncio
async def test_deterministic_experience_and_skill_normalization():
    det_exp = DeterministicJobParser.parse_experience_string("Must have 3+ years of Python development")
    assert det_exp is not None
    assert det_exp["minimum_value"] == 36.0
    assert det_exp["operator"] == "GTE"
    assert det_exp["hard_constraint"] is True

    canonical_rag = SkillNormalizer.normalize("Retrieval Augmented Generation")
    assert canonical_rag == "RAG"

@pytest.mark.asyncio
async def test_protected_feature_filter():
    is_protected_gender, msg1 = ProtectedFeatureFilter.evaluate("Must be a male candidate under 30")
    assert is_protected_gender is True

    is_protected_skill, msg2 = ProtectedFeatureFilter.evaluate("Must have 3+ years of Python experience")
    assert is_protected_skill is False

@pytest.mark.asyncio
async def test_hnsw_job_embedding_index_exists():
    async with async_session_factory() as session:
        query = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'job_embeddings' AND indexname = 'idx_job_embeddings_hnsw';
        """)
        res = (await session.execute(query)).fetchone()
        assert res is not None, "HNSW vector index idx_job_embeddings_hnsw does not exist in PostgreSQL schema!"
        assert "hnsw" in res.indexdef.lower()

@pytest.mark.asyncio
async def test_job_intelligence_tenant_rls_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data_org1 = await _setup_job_intelligence_context(client)
        data_org2 = await _setup_job_intelligence_context(client)

        processor = JobProcessorService()
        await processor.process_job_intelligence(job_id=data_org1["job_id"], organization_id=data_org1["org_id"])

        # Org 2 Recruiter attempting to access Org 1 Job Intelligence -> Denied
        res = await client.get(f"/api/v1/jobs/{data_org1['job_id']}/intelligence", headers=data_org2["rec_headers"])
        assert res.status_code == 404
