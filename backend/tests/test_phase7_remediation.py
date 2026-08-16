import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select

from app.core.config import settings
from app.db.session import async_session_factory
from app.domains.document_intelligence.models import (
    CandidateEmbedding,
    CandidateSkill,
    EvidenceVerificationStatusEnum,
    SkillDurationStatusEnum,
)
from app.domains.identity.models import User
from app.infrastructure.confidence.calculator import ConfidenceCalculator
from app.infrastructure.experience.skill_experience import SkillExperienceCalculator
from app.infrastructure.factories import AIGatewayFactory, EmbeddingProviderFactory
from app.infrastructure.pdf.evidence_verifier import EvidenceVerifier
from app.main import app
from app.services.document_processor import DocumentProcessorService

def _create_dummy_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kinds [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length 120 >> stream\n"
        b"BT /F1 12 Tf 100 700 Td (Senior Software Engineer Resume - Python RAG)\n"
        b"(Acme AI Corp - Senior Architect 2022 to 2025) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer << /Size 5 /Root 1 0 R >>\n"
        b"startxref\n310\n%%EOF"
    )

async def _setup_application_context(client: AsyncClient):
    # Recruiter
    rec_email = f"rec_rem_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter Remediation"})
    rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
    rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

    org_resp = await client.post("/api/v1/organizations", json={"name": "Remediation Org", "slug": f"rem-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    # Admin User for verification
    admin_email = f"admin_rem_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "Password123!", "full_name": "Admin Remediation"})
    admin_login = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    async with async_session_factory() as session:
        await session.begin()
        admin_u = (await session.execute(select(User).where(User.email == admin_email))).scalar_one()
        admin_u.is_platform_admin = True
        await session.commit()

    job_resp = await client.post("/api/v1/jobs", json={"title": "Lead AI Systems Architect", "description": "High performance RAG systems role."}, headers=rec_headers)
    job_id = job_resp.json()["id"]

    await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)
    await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "APPROVE"}, headers=admin_headers)
    await client.post(f"/api/v1/jobs/{job_id}/publish", headers=rec_headers)

    # Candidate
    cand_email = f"cand_rem_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": cand_email, "password": "Password123!", "full_name": "Candidate Remediation"})
    cand_login = await client.post("/api/v1/auth/login", json={"email": cand_email, "password": "Password123!"})
    cand_headers = {"Authorization": f"Bearer {cand_login.json()['access_token']}"}

    async with async_session_factory() as session:
        cand_u = (await session.execute(select(User).where(User.email == cand_email))).scalar_one()
        cand_user_id = cand_u.id

    app_resp = await client.post("/api/v1/candidate/applications", json={"job_id": job_id, "resume_file_path": "resumes/rem.pdf"}, headers=cand_headers)
    application_id = app_resp.json()["id"]

    return {
        "org_id": uuid.UUID(org_id),
        "cand_user_id": cand_user_id,
        "rec_headers": rec_headers,
        "cand_headers": cand_headers,
        "job_id": job_id,
        "application_id": application_id,
    }

@pytest.mark.asyncio
async def test_ai_provider_factory_and_fail_fast_production_credentials(monkeypatch):
    # Testing / Dev environment returns test adapters
    ai_provider = AIGatewayFactory.get_provider()
    emb_provider = EmbeddingProviderFactory.get_provider()
    assert ai_provider.__class__.__name__ in ("TestAIGatewayAdapter", "OpenAIAIGatewayAdapter", "GeminiAIGatewayAdapter")
    assert emb_provider.__class__.__name__ in ("TestEmbeddingAdapter", "OpenAIEmbeddingAdapter", "GeminiEmbeddingAdapter")

    # Staging / Production with placeholder secret must FAIL FAST
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AI_API_KEY", "placeholder_ai_api_key")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "placeholder_gemini_api_key")

    with pytest.raises(ValueError, match="CRITICAL CONFIGURATION ERROR"):
        AIGatewayFactory.get_provider()

    with pytest.raises(ValueError, match="CRITICAL CONFIGURATION ERROR"):
        EmbeddingProviderFactory.get_provider()

@pytest.mark.asyncio
async def test_idempotent_document_reprocessing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_application_context(client)
        pdf_bytes = _create_dummy_pdf_bytes()

        # Initial Upload & Process
        upload_res = await client.post(
            f"/api/v1/applications/{data['application_id']}/documents",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=data["cand_headers"],
        )
        assert upload_res.status_code == 201
        doc_id = uuid.UUID(upload_res.json()["id"])

        async with async_session_factory() as session:
            await session.begin()
            stmt_sk = select(CandidateSkill).where(CandidateSkill.document_id == doc_id)
            skills_pass1 = list((await session.execute(stmt_sk)).scalars().all())
            count_pass1 = len(skills_pass1)

            stmt_emb = select(CandidateEmbedding).where(CandidateEmbedding.document_id == doc_id)
            embs_pass1 = len(list((await session.execute(stmt_emb)).scalars().all()))

        # Re-run Document Processing (Second Time for Same Document)
        processor = DocumentProcessorService()
        await processor.process_document(
            document_id=doc_id,
            organization_id=data["org_id"],
            candidate_id=data["cand_user_id"],
            file_bytes=pdf_bytes,
        )

        async with async_session_factory() as session:
            await session.begin()
            stmt_sk = select(CandidateSkill).where(CandidateSkill.document_id == doc_id)
            skills_pass2 = list((await session.execute(stmt_sk)).scalars().all())
            count_pass2 = len(skills_pass2)

            stmt_emb = select(CandidateEmbedding).where(CandidateEmbedding.document_id == doc_id)
            embs_pass2 = len(list((await session.execute(stmt_emb)).scalars().all()))

        # IDEMPOTENCY VERIFICATION: Count MUST be identical, NOT duplicated!
        assert count_pass2 == count_pass1
        assert embs_pass2 == embs_pass1

@pytest.mark.asyncio
async def test_evidence_verifier_exact_normalized_and_hallucinated_quotes():
    full_text = "5+ years experience building Python microservices with FastAPI and RAG architecture."

    # 1. Exact Match
    status_exact, mult_exact = EvidenceVerifier.verify_evidence("Python microservices", full_text)
    assert status_exact == EvidenceVerificationStatusEnum.VERIFIED
    assert mult_exact == 1.0

    # 2. Case / Whitespace Normalized Match
    status_norm, mult_norm = EvidenceVerifier.verify_evidence("  python   microservices  ", full_text)
    assert status_norm == EvidenceVerificationStatusEnum.VERIFIED
    assert mult_norm == 1.0

    # 3. Token Overlap Match (OCR noise safety)
    status_partial, mult_partial = EvidenceVerifier.verify_evidence("5+ years experience building Python microservices", full_text)
    assert status_partial == EvidenceVerificationStatusEnum.VERIFIED or status_partial == EvidenceVerificationStatusEnum.PARTIALLY_VERIFIED

    # 4. Hallucinated Quote (Does NOT exist in text)
    status_hallucinated, mult_hallucinated = EvidenceVerifier.verify_evidence("10 years Golang backend leadership at Google", full_text)
    assert status_hallucinated == EvidenceVerificationStatusEnum.UNVERIFIED
    assert mult_hallucinated == 0.40

@pytest.mark.asyncio
async def test_independent_confidence_calculator():
    high_conf = ConfidenceCalculator.calculate_confidence(
        llm_confidence=0.95,
        text_quality_score=0.90,
        verified_evidence_ratio=1.0,
        schema_valid=True,
        dates_valid=True,
    )
    assert high_conf["tier"] == "HIGH"
    assert high_conf["final_confidence"] >= 0.85

    low_conf = ConfidenceCalculator.calculate_confidence(
        llm_confidence=0.50,
        text_quality_score=0.20,
        verified_evidence_ratio=0.0,
        schema_valid=False,
        dates_valid=False,
    )
    assert low_conf["tier"] in ("LOW", "UNVERIFIED")
    assert low_conf["final_confidence"] < 0.65

@pytest.mark.asyncio
async def test_hnsw_vector_index_exists_in_database():
    async with async_session_factory() as session:
        query = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'candidate_embeddings' AND indexname = 'idx_candidate_embeddings_hnsw';
        """)
        res = (await session.execute(query)).fetchone()
        assert res is not None, "HNSW vector index idx_candidate_embeddings_hnsw does not exist in PostgreSQL schema!"
        assert "hnsw" in res.indexdef.lower()

@pytest.mark.asyncio
async def test_skill_specific_experience_calculator():
    experiences = [
        {"company_name": "Acme AI", "job_title": "Senior Python Engineer", "evidence_text": "Built Python microservices", "raw_start_date": "2020-01-01", "raw_end_date": "2023-01-01"},
        {"company_name": "Beta Labs", "job_title": "RAG Architect", "evidence_text": "Built RAG systems", "raw_start_date": "2023-01-01", "raw_end_date": "2025-01-01"},
    ]

    # Python is in Employment 1 (3 years)
    py_years, py_status = SkillExperienceCalculator.calculate_skill_experience(
        raw_skill_name="Python",
        canonical_skill_name="Python",
        evidence_text="Built Python microservices",
        experiences=experiences,
    )
    assert py_status == SkillDurationStatusEnum.DETERMINISTIC_CALCULATED
    assert py_years == 3.0

    # Skill mentioned only in summary without specific job linkage
    rust_years, rust_status = SkillExperienceCalculator.calculate_skill_experience(
        raw_skill_name="Rust",
        canonical_skill_name="Rust",
        evidence_text="Interested in learning Rust",
        experiences=experiences,
    )
    assert rust_status == SkillDurationStatusEnum.UNKNOWN
    assert rust_years is None
