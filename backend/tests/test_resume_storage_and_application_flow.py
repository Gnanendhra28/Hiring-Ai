"""
Comprehensive Test Suite for Candidate Resume Upload, Multi-Version Management,
Job Application Binding, and Recruiter Authorized Resume Access.
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application
from app.domains.identity.models import User
from app.domains.jobs.models import Job, JobStatusEnum, JobVerificationStatusEnum
from app.domains.organizations.models import (
    MembershipStatusEnum,
    Organization,
    OrganizationMembership,
    RoleEnum,
)
from app.main import app


# Minimal 1-page valid PDF header bytes
SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
)

# Minimal valid DOCX zip header bytes
SAMPLE_DOCX_BYTES = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00" + (b"0" * 100)


async def _setup_test_context():
    """Sets up Tenant Org, Recruiter, Candidate A, Candidate B, and a Published Job."""
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, is_platform_admin=True)

        # 1. Organization
        org = Organization(
            name=f"Acme Corp {uuid.uuid4().hex[:6]}",
            slug=f"acme-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )
        session.add(org)
        await session.flush()

        # 2. Recruiter User & Membership
        recruiter = User(
            email=f"recruiter_{uuid.uuid4().hex[:6]}@acme.com",
            full_name="Alice Recruiter",
            password_hash="test_hash",
            is_active=True,
        )
        session.add(recruiter)
        await session.flush()

        mem = OrganizationMembership(
            organization_id=org.id,
            user_id=recruiter.id,
            role=RoleEnum.RECRUITER,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(mem)

        # 3. Unrelated Recruiter (Org B)
        org_b = Organization(
            name=f"Other Corp {uuid.uuid4().hex[:6]}",
            slug=f"other-{uuid.uuid4().hex[:6]}",
            is_active=True,
        )
        recruiter_b = User(
            email=f"recruiter_b_{uuid.uuid4().hex[:6]}@other.com",
            full_name="Bob Unauthorized Recruiter",
            password_hash="test_hash",
            is_active=True,
        )
        session.add_all([org_b, recruiter_b])
        await session.flush()

        mem_b = OrganizationMembership(
            organization_id=org_b.id,
            user_id=recruiter_b.id,
            role=RoleEnum.RECRUITER,
            status=MembershipStatusEnum.ACTIVE,
        )
        session.add(mem_b)

        # 4. Candidates
        cand_a = User(
            email=f"cand_a_{uuid.uuid4().hex[:6]}@gmail.com",
            full_name="John Doe Candidate",
            password_hash="test_hash",
            is_active=True,
        )
        cand_b = User(
            email=f"cand_b_{uuid.uuid4().hex[:6]}@gmail.com",
            full_name="Jane Smith Candidate",
            password_hash="test_hash",
            is_active=True,
        )
        session.add_all([cand_a, cand_b])
        await session.flush()

        # 5. Published Job Requisition
        job = Job(
            organization_id=org.id,
            created_by_user_id=recruiter.id,
            title="Senior AI Platform Engineer",
            slug=f"senior-ai-platform-engineer-{uuid.uuid4().hex[:6]}",
            department="Engineering",
            location="Bengaluru, India",
            employment_type="FULL_TIME",
            description="We are hiring a Senior AI Platform Engineer. Experience with Python, PyTorch, and Cloud required.",
            status=JobStatusEnum.PUBLISHED,
            verification_status=JobVerificationStatusEnum.APPROVED,
        )
        session.add(job)
        await session.commit()

        return {
            "org_id": str(org.id),
            "job_id": str(job.id),
            "recruiter_token": create_access_token(recruiter.id),
            "recruiter_b_token": create_access_token(recruiter_b.id),
            "cand_a_token": create_access_token(cand_a.id),
            "cand_b_token": create_access_token(cand_b.id),
            "cand_a_id": str(cand_a.id),
            "cand_b_id": str(cand_b.id),
        }


@pytest.mark.asyncio
async def test_01_candidate_upload_resume_success():
    """Verifies candidate can successfully upload valid PDF and DOCX resumes with versioning."""
    ctx = await _setup_test_context()
    headers = {"Authorization": f"Bearer {ctx['cand_a_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Upload Resume 1 (PDF)
        files = {"file": ("software_engineer_resume.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
        resp1 = await client.post("/api/v1/resumes/upload", headers=headers, files=files)
        assert resp1.status_code == 201
        data1 = resp1.json()
        assert data1["file_name"] == "software_engineer_resume.pdf"
        assert data1["version"] >= 1
        assert data1["content_type"] == "application/pdf"
        assert data1["resume_id"] is not None

        # Upload Resume 2 (DOCX)
        files_docx = {"file": ("ai_specialist_resume.docx", SAMPLE_DOCX_BYTES, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        resp2 = await client.post("/api/v1/resumes/upload", headers=headers, files=files_docx)
        assert resp2.status_code == 201
        data2 = resp2.json()
        assert data2["file_name"] == "ai_specialist_resume.docx"
        assert data2["version"] >= 2
        assert data2["resume_id"] != data1["resume_id"]


@pytest.mark.asyncio
async def test_02_invalid_file_type_rejected():
    """Verifies that executables or unsupported file types are rejected with HTTP 415."""
    ctx = await _setup_test_context()
    headers = {"Authorization": f"Bearer {ctx['cand_a_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fake_exe = b"MZ\x90\x00\x03\x00\x00\x00" + b"malicious executable payload"
        files = {"file": ("malicious_payload.exe", fake_exe, "application/octet-stream")}
        resp = await client.post("/api/v1/resumes/upload", headers=headers, files=files)
        assert resp.status_code == 415
        assert "Unsupported file format" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_03_oversized_file_rejected():
    """Verifies that files exceeding 10MB limit are rejected with HTTP 413."""
    ctx = await _setup_test_context()
    headers = {"Authorization": f"Bearer {ctx['cand_a_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        huge_content = SAMPLE_PDF_BYTES + (b"0" * (11 * 1024 * 1024))
        files = {"file": ("huge_resume.pdf", huge_content, "application/pdf")}
        resp = await client.post("/api/v1/resumes/upload", headers=headers, files=files)
        assert resp.status_code == 413
        assert "exceeds maximum allowed limit" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_04_candidate_cannot_access_another_candidates_resume():
    """Verifies candidate A cannot download or view candidate B's resume."""
    ctx = await _setup_test_context()
    headers_b = {"Authorization": f"Bearer {ctx['cand_b_token']}"}
    headers_a = {"Authorization": f"Bearer {ctx['cand_a_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Candidate B uploads a resume
        files = {"file": ("jane_private_resume.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
        resp_b = await client.post("/api/v1/resumes/upload", headers=headers_b, files=files)
        assert resp_b.status_code == 201
        resume_id_b = resp_b.json()["resume_id"]

        # Candidate A tries to access Candidate B's resume -> 403 Forbidden
        resp_attack = await client.get(f"/api/v1/resumes/{resume_id_b}", headers=headers_a)
        assert resp_attack.status_code == 403

        # Candidate A tries to download Candidate B's resume file -> 403 Forbidden
        resp_dl_attack = await client.get(f"/api/v1/resumes/{resume_id_b}/file", headers=headers_a)
        assert resp_dl_attack.status_code == 403


@pytest.mark.asyncio
async def test_05_and_06_application_stores_selected_resume_version_immutably():
    """Verifies that an application stores the chosen resume version and is not altered when newer resumes are uploaded."""
    ctx = await _setup_test_context()
    headers_a = {"Authorization": f"Bearer {ctx['cand_a_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Candidate A uploads Resume 1 (Version 1)
        files_v1 = {"file": ("john_doe_v1.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
        r1 = await client.post("/api/v1/resumes/upload", headers=headers_a, files=files_v1)
        resume_v1_id = r1.json()["resume_id"]

        # 2. Candidate A applies to Job with Resume Version 1
        apply_payload = {
            "job_id": ctx["job_id"],
            "resume_id": resume_v1_id,
        }
        resp_app = await client.post("/api/v1/candidate/applications", headers=headers_a, json=apply_payload)
        assert resp_app.status_code == 201
        app_data = resp_app.json()
        application_id = app_data["id"]
        assert app_data["resume_id"] == resume_v1_id

        # 3. Later, Candidate A uploads Resume 2 (Version 2)
        files_v2 = {"file": ("john_doe_v2_updated.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
        r2 = await client.post("/api/v1/resumes/upload", headers=headers_a, files=files_v2)
        resume_v2_id = r2.json()["resume_id"]
        assert resume_v2_id != resume_v1_id

        # 4. Verify existing application STILL points to Resume Version 1 (Immutable Reference)
        async with async_session_factory() as session:
            await set_tenant_context(session, is_platform_admin=True)
            stmt = select(Application).where(Application.id == uuid.UUID(application_id))
            saved_app = (await session.execute(stmt)).scalar_one()
            assert str(saved_app.resume_id) == str(resume_v1_id)


@pytest.mark.asyncio
async def test_07_authorized_recruiter_can_access_submitted_resume():
    """Verifies that an authorized recruiter managing the job can access the applicant's submitted resume."""
    ctx = await _setup_test_context()
    headers_a = {"Authorization": f"Bearer {ctx['cand_a_token']}"}
    headers_rec = {"Authorization": f"Bearer {ctx['recruiter_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Candidate applies
        files = {"file": ("john_ai_resume.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
        r = await client.post("/api/v1/resumes/upload", headers=headers_a, files=files)
        resume_id = r.json()["resume_id"]

        app_resp = await client.post(
            "/api/v1/candidate/applications",
            headers=headers_a,
            json={"job_id": ctx["job_id"], "resume_id": resume_id},
        )
        app_id = app_resp.json()["id"]

        # Authorized Recruiter requests resume access metadata & signed URL
        resp_access = await client.get(f"/api/v1/jobs/applications/{app_id}/resume/access", headers=headers_rec)
        assert resp_access.status_code == 200
        access_info = resp_access.json()
        assert access_info["resume_id"] == resume_id
        assert access_info["application_id"] == app_id
        assert "access_url" in access_info

        # Authorized Recruiter streams the actual resume PDF
        resp_stream = await client.get(f"/api/v1/jobs/applications/{app_id}/resume", headers=headers_rec)
        assert resp_stream.status_code == 200
        assert resp_stream.headers.get("content-type") == "application/pdf"
        assert len(resp_stream.content) > 0


@pytest.mark.asyncio
async def test_08_unauthorized_recruiter_denied_access():
    """Verifies that an unauthorized recruiter from another organization cannot access the candidate's resume."""
    ctx = await _setup_test_context()
    headers_a = {"Authorization": f"Bearer {ctx['cand_a_token']}"}
    headers_rec_b = {"Authorization": f"Bearer {ctx['recruiter_b_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Candidate applies to Org A's job
        files = {"file": ("john_private_cv.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
        r = await client.post("/api/v1/resumes/upload", headers=headers_a, files=files)
        resume_id = r.json()["resume_id"]

        app_resp = await client.post(
            "/api/v1/candidate/applications",
            headers=headers_a,
            json={"job_id": ctx["job_id"], "resume_id": resume_id},
        )
        app_id = app_resp.json()["id"]

        # Recruiter B (Org B) attempts access -> 403 Forbidden
        resp_denied = await client.get(f"/api/v1/jobs/applications/{app_id}/resume", headers=headers_rec_b)
        assert resp_denied.status_code == 403
        detail_msg = resp_denied.json().get("detail", "").lower()
        assert any(term in detail_msg for term in ["not authorized", "denied", "forbidden", "requires"])


@pytest.mark.asyncio
async def test_09_direct_arbitrary_resume_access_denied():
    """Verifies that a user attempting to query non-existent or arbitrary resume IDs is denied."""
    ctx = await _setup_test_context()
    headers_rec = {"Authorization": f"Bearer {ctx['recruiter_token']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        arbitrary_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/jobs/applications/{arbitrary_id}/resume", headers=headers_rec)
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_10_authentication_token_validation():
    """Verifies unauthenticated requests (missing or forged tokens) are rejected with 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # No token
        resp1 = await client.get("/api/v1/resumes")
        assert resp1.status_code == 401

        # Forged token
        resp2 = await client.get("/api/v1/resumes", headers={"Authorization": "Bearer forged_invalid_token_xyz"})
        assert resp2.status_code == 401
