import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.main import app

@pytest.mark.asyncio
async def test_dashboard_real_db_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register Recruiter & Admin
        rec_email = f"rec_dash_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter Dash"})
        rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
        rec_token = rec_login.json()["access_token"]
        rec_headers = {"Authorization": f"Bearer {rec_token}"}

        admin_email = f"admin_dash_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "Password123!", "full_name": "Admin Dash"})
        admin_login = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password123!"})
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        async with async_session_factory() as session:
            await session.begin()
            user = (await session.execute(select(User).where(User.email == admin_email))).scalar_one()
            user.is_platform_admin = True
            await session.commit()

        # Create Organization
        org_resp = await client.post("/api/v1/organizations", json={"name": "Metrics Corp", "slug": f"metrics-corp-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
        rec_headers["X-Organization-ID"] = org_resp.json()["id"]

        # Initial metrics (all counts 0)
        init_metrics = await client.get("/api/v1/dashboard/metrics", headers=rec_headers)
        assert init_metrics.status_code == 200
        assert init_metrics.json()["active_jobs_count"] == 0
        assert init_metrics.json()["draft_jobs_count"] == 0

        # Create 1 DRAFT job
        await client.post("/api/v1/jobs", json={"title": "Draft Backend Dev", "description": "Draft backend job description."}, headers=rec_headers)

        # Create 2 Jobs, Verify, and Publish them
        j1 = (await client.post("/api/v1/jobs", json={"title": "Verified Active Dev 1", "description": "Active job 1 description."}, headers=rec_headers)).json()
        await client.post(f"/api/v1/jobs/{j1['id']}/submit-verification", headers=rec_headers)
        await client.post(f"/api/v1/admin/jobs/{j1['id']}/verify", json={"action": "APPROVE"}, headers=admin_headers)
        await client.post(f"/api/v1/jobs/{j1['id']}/publish", headers=rec_headers)

        j2 = (await client.post("/api/v1/jobs", json={"title": "Verified Active Dev 2", "description": "Active job 2 description."}, headers=rec_headers)).json()
        await client.post(f"/api/v1/jobs/{j2['id']}/submit-verification", headers=rec_headers)
        await client.post(f"/api/v1/admin/jobs/{j2['id']}/verify", json={"action": "APPROVE"}, headers=admin_headers)
        await client.post(f"/api/v1/jobs/{j2['id']}/publish", headers=rec_headers)

        # Fetch updated real DB metrics
        metrics_resp = await client.get("/api/v1/dashboard/metrics", headers=rec_headers)
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.json()

        # Real DB Counts assertion
        assert metrics["active_jobs_count"] == 2
        assert metrics["draft_jobs_count"] == 1
        assert len(metrics["recent_jobs"]) == 3
