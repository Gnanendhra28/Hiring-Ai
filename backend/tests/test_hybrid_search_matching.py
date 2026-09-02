"""
Test Suite for Hybrid Search & Anti-Hallucination Matching Engine.
Verifies:
1. BM25 sparse token scoring
2. Strict evidence grounding (no hallucination)
3. Normalized synonym domain cluster matching
4. Reciprocal Rank & Weighted Score Fusion
5. Hard eligibility filtering
6. API endpoint integration
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.organizations.models import (
    MembershipStatusEnum,
    Organization,
    OrganizationMembership,
    RoleEnum,
)
from app.infrastructure.matching.hybrid_search_engine import (
    HybridSearchAndMatchingEngine,
)
from app.main import app


def test_01_bm25_token_scoring():
    """Verifies BM25 token scoring correctly rewards document keyword density."""
    query = ["Python", "FastAPI", "PostgreSQL", "Docker"]
    doc_perfect = "Senior backend engineer with 6 years experience in Python, FastAPI, PostgreSQL, Docker, and Kubernetes."
    doc_poor = "Marketing specialist with experience in social media and content writing."

    score_perfect = HybridSearchAndMatchingEngine.compute_bm25_token_score(query, doc_perfect)
    score_poor = HybridSearchAndMatchingEngine.compute_bm25_token_score(query, doc_poor)

    assert score_perfect > 70.0
    assert score_poor == 0.0


def test_02_evidence_grounding_prevents_hallucination():
    """Verifies that missing skills are explicitly flagged as MISSING without hallucinated points."""
    required = ["Python", "Kubernetes", "Golang", "Rust"]
    preferred = ["GraphQL"]
    candidate_skills = ["Python", "Django", "PostgreSQL"]
    candidate_text = "Experienced software developer specialized in Python backend development and relational databases."

    coverage, citations, missing, eligibility, reasons = HybridSearchAndMatchingEngine.verify_evidence_grounding(
        required_items=required,
        preferred_items=preferred,
        candidate_skills=candidate_skills,
        candidate_text=candidate_text,
    )

    # Only Python was matched (1 out of 4 = 25%)
    assert coverage == 25.0
    assert "Kubernetes" in missing
    assert "Golang" in missing
    assert "Rust" in missing
    assert eligibility == "FAIL"  # Less than 50% required skills matched

    python_citation = next((c for c in citations if c.requirement == "Python"), None)
    assert python_citation is not None
    assert python_citation.match_type == "EXACT_KEYWORD"
    assert python_citation.confidence == 1.0


def test_03_synonym_cluster_equivalence():
    """Verifies that domain synonyms (e.g. Postgres -> PostgreSQL, GenAI -> Generative AI) match accurately."""
    required = ["PostgreSQL", "Generative AI"]
    preferred = []
    candidate_skills = ["Postgres", "GenAI"]
    candidate_text = "AI engineer working with Postgres and GenAI models."

    coverage, citations, missing, eligibility, reasons = HybridSearchAndMatchingEngine.verify_evidence_grounding(
        required_items=required,
        preferred_items=preferred,
        candidate_skills=candidate_skills,
        candidate_text=candidate_text,
    )

    assert coverage == 100.0
    assert len(missing) == 0
    assert eligibility == "PASS"


@pytest.mark.asyncio
async def test_04_hybrid_match_api_endpoint():
    """Verifies recruiter can call GET /api/v1/jobs/{job_id}/matching/hybrid/{candidate_id}."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        org = Organization(name=f"Org {uuid.uuid4().hex[:6]}", slug=f"org-{uuid.uuid4().hex[:6]}", is_active=True)
        recruiter = User(email=f"rec_{uuid.uuid4().hex[:6]}@test.com", password_hash="hash", full_name="Recruiter", is_active=True)
        candidate = User(email=f"cand_{uuid.uuid4().hex[:6]}@test.com", password_hash="hash", full_name="Candidate", is_active=True)
        session.add_all([org, recruiter, candidate])
        await session.flush()

        mem = OrganizationMembership(organization_id=org.id, user_id=recruiter.id, role=RoleEnum.RECRUITER, status=MembershipStatusEnum.ACTIVE)
        session.add(mem)

        job = Job(
            organization_id=org.id,
            created_by_user_id=recruiter.id,
            title="Senior Full Stack Engineer",
            slug=f"senior-full-stack-{uuid.uuid4().hex[:6]}",
            department="Engineering",
            location="Remote",
            employment_type="FULL_TIME",
            description="We are looking for a Senior Full Stack Engineer. Required: Python, React, PostgreSQL.",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.commit()

        token = create_access_token(recruiter.id)
        job_id = str(job.id)
        candidate_id = str(candidate.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/jobs/{job_id}/matching/hybrid/{candidate_id}",
            headers={"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "hybrid_fused_score" in data
        assert "sparse_lexical_score" in data
        assert "dense_semantic_score" in data
        assert data["is_hallucination_guarded"] is True
        assert data["fusion_algorithm"] == "Reciprocal_Rank_Weighted_Fusion"
