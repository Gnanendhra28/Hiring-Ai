import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.main import app

async def _create_approved_admin_client(client: AsyncClient, email: str):
    await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Admin User"})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
    token = login.json()["access_token"]
    async with async_session_factory() as session:
        await session.begin()
        user = (await session.execute(select(User).where(User.email == email))).scalar_one()
        user.is_platform_admin = True
        await session.commit()
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_public_job_directory_filters_draft_jobs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register Admin & Recruiter
        admin_headers = await _create_approved_admin_client(client, f"admin_pub_{uuid.uuid4().hex[:8]}@example.com")

        rec_email = f"recruiter_pub_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Public Recruiter"})
        login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
        rec_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        org_resp = await client.post("/api/v1/organizations", json={"name": "Public Corp", "slug": f"pub-corp-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
        org_id = org_resp.json()["id"]
        rec_headers["X-Organization-ID"] = org_id

        # 1. Create DRAFT job (remains unverified DRAFT)
        await client.post("/api/v1/jobs", json={"title": "Private Draft Engineer", "description": "Internal brief for draft role."}, headers=rec_headers)

        # 2. Create, Verify, and Publish Public Job
        pub_job_resp = await client.post("/api/v1/jobs", json={"title": "Public Staff Architect", "description": "Public specification for staff architect."}, headers=rec_headers)
        pub_job_id = pub_job_resp.json()["id"]

        await client.post(f"/api/v1/jobs/{pub_job_id}/submit-verification", headers=rec_headers)
        await client.post(f"/api/v1/admin/jobs/{pub_job_id}/verify", json={"action": "APPROVE"}, headers=admin_headers)
        pub_job = (await client.post(f"/api/v1/jobs/{pub_job_id}/publish", headers=rec_headers)).json()

        # 3. Query Public Job Directory (NO AUTH REQUIRED)
        public_resp = await client.get("/api/v1/jobs/public")
        assert public_resp.status_code == 200
        public_data = public_resp.json()

        # Verify ONLY the APPROVED & PUBLISHED job is visible
        public_titles = [item["title"] for item in public_data["items"]]
        assert "Public Staff Architect" in public_titles
        assert "Private Draft Engineer" not in public_titles

        # 4. Query Public Job Detail by Slug
        slug_resp = await client.get(f"/api/v1/jobs/public/{pub_job['slug']}")
        assert slug_resp.status_code == 200
        assert slug_resp.json()["title"] == "Public Staff Architect"

@pytest.mark.asyncio
async def test_application_submission_and_duplicate_prevention():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        admin_headers = await _create_approved_admin_client(client, f"admin_app_{uuid.uuid4().hex[:8]}@example.com")

        # Register Recruiter & Create Approved Published Job
        rec_email = f"rec_app_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter App"})
        rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
        rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

        org_resp = await client.post("/api/v1/organizations", json={"name": "App Corp", "slug": f"app-corp-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
        rec_headers["X-Organization-ID"] = org_resp.json()["id"]

        job_resp = await client.post("/api/v1/jobs", json={"title": "Full Stack Dev", "description": "Building hiring software."}, headers=rec_headers)
        job_id = job_resp.json()["id"]

        await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)
        await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "APPROVE"}, headers=admin_headers)
        await client.post(f"/api/v1/jobs/{job_id}/publish", headers=rec_headers)

        # Register Candidate User
        cand_email = f"candidate_{uuid.uuid4().hex[:8]}@example.com"
        cand_reg = await client.post("/api/v1/auth/register", json={"email": cand_email, "password": "Password123!", "full_name": "Jane Candidate"})
        assert cand_reg.status_code == 201

        cand_login = await client.post("/api/v1/auth/login", json={"email": cand_email, "password": "Password123!"})
        cand_headers = {"Authorization": f"Bearer {cand_login.json()['access_token']}"}

        # Candidate updates profile
        prof_resp = await client.put("/api/v1/candidate/profile", json={"headline": "Senior Full-Stack Developer", "skills": ["Python", "FastAPI", "React"]}, headers=cand_headers)
        assert prof_resp.status_code == 200

        # Submit Application 1
        app_payload = {"job_id": job_id, "resume_file_path": "candidates/docs/resume.pdf"}
        app_resp = await client.post("/api/v1/candidate/applications", json=app_payload, headers=cand_headers)
        assert app_resp.status_code == 201
        app_data = app_resp.json()
        assert app_data["status"] == "SUBMITTED"

        # CRITICAL TEST: Attempt Duplicate Application -> MUST FAIL WITH HTTP 400 BAD REQUEST
        dup_resp = await client.post("/api/v1/candidate/applications", json=app_payload, headers=cand_headers)
        assert dup_resp.status_code == 400
        assert "Duplicate Application" in dup_resp.json()["detail"]

        # Candidate lists own applications
        my_apps_resp = await client.get("/api/v1/candidate/applications", headers=cand_headers)
        assert my_apps_resp.status_code == 200
        my_apps = my_apps_resp.json()
        assert len(my_apps) == 1
        assert my_apps[0]["id"] == app_data["id"]

        # Recruiter lists applications for job -> Default status is SUBMITTED
        rec_list_resp = await client.get(f"/api/v1/jobs/{job_id}/applications", headers=rec_headers)
        assert rec_list_resp.status_code == 200
        rec_apps = rec_list_resp.json()["items"]
        assert len(rec_apps) == 1
        app_id = rec_apps[0]["id"]
        assert rec_apps[0]["status"] == "SUBMITTED"

        # Recruiter updates status through required lifecycle: REVIEWED -> SHORTLISTED -> INTERVIEW -> SELECTED
        for new_st in ["REVIEWED", "SHORTLISTED", "INTERVIEW", "SELECTED"]:
            upd_resp = await client.put(f"/api/v1/jobs/{job_id}/applications/{app_id}/status", json={"status": new_st}, headers=rec_headers)
            assert upd_resp.status_code == 200
            assert upd_resp.json()["status"] == new_st

            # Verify status persists on reload
            check_resp = await client.get(f"/api/v1/jobs/{job_id}/applications", headers=rec_headers)
            assert check_resp.json()["items"][0]["status"] == new_st
