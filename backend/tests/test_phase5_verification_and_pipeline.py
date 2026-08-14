import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.main import app

@pytest.mark.asyncio
async def test_recruiter_cannot_directly_publish_unverified_job():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register Recruiter & Create Org
        email = f"rec_verif_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Recruiter Verification"})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123!"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        org_resp = await client.post("/api/v1/organizations", json={"name": "Verif Org", "slug": f"verif-org-{uuid.uuid4().hex[:6]}"}, headers=headers)
        headers["X-Organization-ID"] = org_resp.json()["id"]

        # 1. Create Job (Default: DRAFT, DRAFT)
        job_resp = await client.post("/api/v1/jobs", json={"title": "Unverified Engineer", "description": "Needs verification."}, headers=headers)
        assert job_resp.status_code == 201
        job = job_resp.json()
        assert job["verification_status"] == "DRAFT"

        # 2. CRITICAL TEST: Attempt to publish unverified job -> MUST return 403 Forbidden
        pub_resp = await client.post(f"/api/v1/jobs/{job['id']}/publish", headers=headers)
        assert pub_resp.status_code == 403
        assert "Job Verification Required" in pub_resp.json()["detail"]

@pytest.mark.asyncio
async def test_admin_approve_and_publish_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register Recruiter & Create Org & Job
        rec_email = f"rec_workflow_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter Workflow"})
        rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
        rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

        org_resp = await client.post("/api/v1/organizations", json={"name": "Workflow Corp", "slug": f"wf-corp-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
        rec_headers["X-Organization-ID"] = org_resp.json()["id"]

        job_resp = await client.post("/api/v1/jobs", json={"title": "Approved Principal Architect", "description": "Fully compliant spec."}, headers=rec_headers)
        job_id = job_resp.json()["id"]

        # Recruiter submits for verification
        sub_resp = await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)
        assert sub_resp.status_code == 200
        assert sub_resp.json()["verification_status"] == "PENDING_VERIFICATION"

        # 2. Create Platform Admin User directly in DB
        admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "Password123!", "full_name": "System Admin"})
        admin_login = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password123!"})
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Promote admin_email to is_platform_admin = True in DB
        async with async_session_factory() as session:
            await session.begin()
            stmt = select(User).where(User.email == admin_email)
            admin_user = (await session.execute(stmt)).scalar_one()
            admin_user.is_platform_admin = True
            await session.commit()

        # Admin fetches pending jobs
        pending_resp = await client.get("/api/v1/admin/jobs/pending", headers=admin_headers)
        assert pending_resp.status_code == 200
        pending_ids = [j["id"] for j in pending_resp.json()["items"]]
        assert job_id in pending_ids

        # Admin approves job
        verify_resp = await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "APPROVE"}, headers=admin_headers)
        assert verify_resp.status_code == 200
        assert verify_resp.json()["verification_status"] == "APPROVED"

        # 3. Recruiter can now publish job
        pub_resp = await client.post(f"/api/v1/jobs/{job_id}/publish", headers=rec_headers)
        assert pub_resp.status_code == 200
        assert pub_resp.json()["status"] == "PUBLISHED"

        # 4. Verify Public API lists published job
        public_resp = await client.get("/api/v1/jobs/public")
        assert public_resp.status_code == 200
        pub_titles = [j["title"] for j in public_resp.json()["items"]]
        assert "Approved Principal Architect" in pub_titles

@pytest.mark.asyncio
async def test_admin_reject_job_and_resubmission():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register Recruiter & Create Job
        rec_email = f"rec_rej_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter Reject"})
        rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
        rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

        org_resp = await client.post("/api/v1/organizations", json={"name": "Rej Corp", "slug": f"rej-corp-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
        rec_headers["X-Organization-ID"] = org_resp.json()["id"]

        job_resp = await client.post("/api/v1/jobs", json={"title": "Vague Role", "description": "Too brief."}, headers=rec_headers)
        job_id = job_resp.json()["id"]
        await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)

        # Register Admin & promote
        admin_email = f"admin_rej_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "Password123!", "full_name": "Admin Rej"})
        admin_login = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password123!"})
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        async with async_session_factory() as session:
            await session.begin()
            admin_user = (await session.execute(select(User).where(User.email == admin_email))).scalar_one()
            admin_user.is_platform_admin = True
            await session.commit()

        # Admin rejects job without reason -> MUST FAIL with 400 Bad Request
        fail_rej = await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "REJECT"}, headers=admin_headers)
        assert fail_rej.status_code == 400

        # Admin rejects with reason
        rej_resp = await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "REJECT", "rejection_reason": "Description is vague. Please add responsibilities."}, headers=admin_headers)
        assert rej_resp.status_code == 200
        assert rej_resp.json()["verification_status"] == "REJECTED"
        assert rej_resp.json()["rejection_reason"] == "Description is vague. Please add responsibilities."

        # Recruiter resubmits after fix
        resub = await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)
        assert resub.status_code == 200
        assert resub.json()["verification_status"] == "PENDING_VERIFICATION"
        assert resub.json()["rejection_reason"] is None
