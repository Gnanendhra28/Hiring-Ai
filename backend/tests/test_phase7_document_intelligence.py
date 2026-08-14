import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.infrastructure.experience.calculator import ExperienceCalculator
from app.infrastructure.skills.normalizer import SkillNormalizer
from app.main import app

def _create_dummy_pdf_bytes() -> bytes:
    # Construct a minimal valid PDF byte string
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kinds [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length 55 >> stream\n"
        b"BT /F1 12 Tf 100 700 Td (Senior Software Engineer Resume - Python RAG) Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer << /Size 5 /Root 1 0 R >>\n"
        b"startxref\n310\n%%EOF"
    )
    return pdf_content

async def _setup_application_context(client: AsyncClient):
    # Recruiter
    rec_email = f"rec_p7_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter P7"})
    rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
    rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

    org_resp = await client.post("/api/v1/organizations", json={"name": "DocIntel Org", "slug": f"doc-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    # Admin User for verification
    admin_email = f"admin_p7_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "Password123!", "full_name": "Admin P7"})
    admin_login = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    async with async_session_factory() as session:
        await session.begin()
        admin_u = (await session.execute(select(User).where(User.email == admin_email))).scalar_one()
        admin_u.is_platform_admin = True
        await session.commit()

    job_resp = await client.post("/api/v1/jobs", json={"title": "AI Systems Architect", "description": "High performance RAG systems role."}, headers=rec_headers)
    job_id = job_resp.json()["id"]

    await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)
    await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "APPROVE"}, headers=admin_headers)
    await client.post(f"/api/v1/jobs/{job_id}/publish", headers=rec_headers)

    # Candidate
    cand_email = f"cand_p7_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": cand_email, "password": "Password123!", "full_name": "Candidate P7"})
    cand_login = await client.post("/api/v1/auth/login", json={"email": cand_email, "password": "Password123!"})
    cand_headers = {"Authorization": f"Bearer {cand_login.json()['access_token']}"}

    app_resp = await client.post("/api/v1/candidate/applications", json={"job_id": job_id, "resume_file_path": "resumes/p7.pdf"}, headers=cand_headers)
    application_id = app_resp.json()["id"]

    return {
        "rec_headers": rec_headers,
        "cand_headers": cand_headers,
        "job_id": job_id,
        "application_id": application_id,
    }

@pytest.mark.asyncio
async def test_pdf_upload_validation_and_async_processing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_application_context(client)

        pdf_bytes = _create_dummy_pdf_bytes()

        # 1. Reject Non-PDF File
        non_pdf_resp = await client.post(
            f"/api/v1/applications/{data['application_id']}/documents",
            files={"file": ("resume.txt", b"Hello World Plain Text", "text/plain")},
            headers=data["cand_headers"],
        )
        assert non_pdf_resp.status_code == 400
        assert "Invalid file type" in non_pdf_resp.json()["detail"]

        # 2. Reject Malformed PDF (wrong magic header)
        bad_magic_resp = await client.post(
            f"/api/v1/applications/{data['application_id']}/documents",
            files={"file": ("resume.pdf", b"NOT_A_PDF_HEADER", "application/pdf")},
            headers=data["cand_headers"],
        )
        assert bad_magic_resp.status_code == 400
        assert "Malformed document" in bad_magic_resp.json()["detail"]

        # 3. Successful PDF Resume Upload & Processing
        valid_resp = await client.post(
            f"/api/v1/applications/{data['application_id']}/documents",
            files={"file": ("candidate_resume.pdf", pdf_bytes, "application/pdf")},
            headers=data["cand_headers"],
        )
        assert valid_resp.status_code == 201
        doc_data = valid_resp.json()
        assert doc_data["processing_status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_skill_normalization_and_non_equivalency_guard():
    # Skill Normalization
    assert SkillNormalizer.normalize("retrieval augmented generation") == "RAG"
    assert SkillNormalizer.normalize("python3") == "Python"
    assert SkillNormalizer.normalize("postgres db") == "PostgreSQL"
    assert SkillNormalizer.normalize("fast api") == "FastAPI"

    # Non-Equivalency Guard
    assert SkillNormalizer.are_equivalent("RAG", "retrieval-augmented generation") is True
    assert SkillNormalizer.are_equivalent("RAG", "ChatGPT") is False
    assert SkillNormalizer.are_equivalent("Kubernetes", "Docker") is False

@pytest.mark.asyncio
async def test_deterministic_experience_calculator_with_overlapping_ranges():
    experiences = [
        {"raw_start_date": "2020-01-01", "raw_end_date": "2023-01-01", "is_current": False},
        {"raw_start_date": "2022-01-01", "raw_end_date": "2024-01-01", "is_current": False},  # 1 year overlap with previous
    ]
    res = ExperienceCalculator.calculate_total_experience(experiences)
    # Merged period: 2020-01-01 to 2024-01-01 -> 48 months (4.0 years)
    assert res["total_months"] == 48
    assert res["total_years"] == 4.0
    assert res["merged_periods_count"] == 1

@pytest.mark.asyncio
async def test_recruiter_evidence_retrieval_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_application_context(client)

        pdf_bytes = _create_dummy_pdf_bytes()
        upload_res = await client.post(
            f"/api/v1/applications/{data['application_id']}/documents",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=data["cand_headers"],
        )
        assert upload_res.status_code == 201

        # Recruiter views candidate document evidence
        intel_resp = await client.get(
            f"/api/v1/applications/{data['application_id']}/intelligence",
            headers=data["rec_headers"],
        )
        assert intel_resp.status_code == 200
        intel = intel_resp.json()
        assert intel["processing_status"] == "COMPLETED"
        assert len(intel["skills"]) > 0
        assert len(intel["experiences"]) > 0
        assert len(intel["educations"]) > 0

        # Verify evidence quotes exist
        first_skill = intel["skills"][0]
        assert "evidence_text" in first_skill and first_skill["evidence_text"] is not None
        assert "canonical_skill_name" in first_skill
