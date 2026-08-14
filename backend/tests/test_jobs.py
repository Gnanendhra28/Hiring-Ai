import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_job_crud_and_tenant_rls_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register User 1 & Org A
        email1 = f"recruiter1_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": email1, "password": "Password123!", "full_name": "Recruiter 1"})
        login1 = await client.post("/api/v1/auth/login", json={"email": email1, "password": "Password123!"})
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        org_a_resp = await client.post("/api/v1/organizations", json={"name": "TechCorp Org A", "slug": f"techcorp-a-{uuid.uuid4().hex[:6]}"}, headers=headers1)
        org_a_id = org_a_resp.json()["id"]
        headers1["X-Organization-ID"] = org_a_id

        # 2. User 1 creates Job in Org A
        job_payload = {
            "title": "Senior Python Engineer",
            "description": "Designing high-scale microservices with FastAPI and PostgreSQL.",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "FULL_TIME",
            "status": "PUBLISHED"
        }
        create_job_resp = await client.post("/api/v1/jobs", json=job_payload, headers=headers1)
        assert create_job_resp.status_code == 201
        job_a = create_job_resp.json()
        assert job_a["title"] == "Senior Python Engineer"
        assert job_a["organization_id"] == org_a_id

        # 3. List Jobs under Org A
        list_resp = await client.get("/api/v1/jobs", headers=headers1)
        assert list_resp.status_code == 200
        jobs_data = list_resp.json()
        assert jobs_data["total"] == 1
        assert jobs_data["items"][0]["id"] == job_a["id"]

        # 4. Register User 2 & Org B
        email2 = f"recruiter2_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={"email": email2, "password": "Password123!", "full_name": "Recruiter 2"})
        login2 = await client.post("/api/v1/auth/login", json={"email": email2, "password": "Password123!"})
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        org_b_resp = await client.post("/api/v1/organizations", json={"name": "DevCorp Org B", "slug": f"devcorp-b-{uuid.uuid4().hex[:6]}"}, headers=headers2)
        org_b_id = org_b_resp.json()["id"]
        headers2["X-Organization-ID"] = org_b_id

        # 5. User 2 lists jobs in Org B -> MUST BE 0 (RLS Isolation)
        list_b_resp = await client.get("/api/v1/jobs", headers=headers2)
        assert list_b_resp.status_code == 200
        assert list_b_resp.json()["total"] == 0

        # 6. User 2 attempts to fetch Org A's Job ID under Org B context -> MUST BE 404 NOT FOUND (RLS Filtered)
        get_b_resp = await client.get(f"/api/v1/jobs/{job_a['id']}", headers=headers2)
        assert get_b_resp.status_code == 404
