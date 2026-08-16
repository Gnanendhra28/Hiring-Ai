import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.domains.identity.models import User
from app.domains.candidates.models import CandidateProfile
from app.core.security import create_access_token
from app.db.session import async_session_factory
from sqlalchemy import select

@pytest.mark.asyncio
async def test_unauthenticated_candidate_profile_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/candidate/profile")
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_candidate_read_and_update_own_profile():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create test candidate user
        cand_id = uuid.uuid4()
        async with async_session_factory() as session:
            cand_user = User(
                id=cand_id,
                email=f"cand_profile_{cand_id.hex[:6]}@example.com",
                password_hash="fakehash123",
                full_name="Profile Candidate",
                is_platform_admin=False,
                is_active=True,
                is_verified=True,
            )
            session.add(cand_user)
            await session.commit()

        token = create_access_token(user_id=cand_id)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET /api/v1/candidate/profile (creates profile on demand)
        get_resp = await client.get("/api/v1/candidate/profile", headers=headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["user_id"] == str(cand_id)

        # 2. PUT /api/v1/candidate/profile (updates all structured sections)
        update_payload = {
            "headline": "Senior AI Systems Engineer",
            "location": "San Francisco, CA",
            "phone": "+91 98765 43210",
            "degree": "B.Tech / B.E.",
            "college": "Indian Institute of Technology (IIT), Bhilai",
            "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "education": [{
                "degree": "B.Tech",
                "institution": "IIT Bhilai",
                "field": "Computer Science",
                "start_year": "2022",
                "end_year": "2026",
                "grade": "9.1/10"
            }],
            "career_preferences": {
                "job_type": "Full-time Jobs",
                "locations": "Bengaluru, Remote",
                "availability": "Immediate",
                "work_mode": "Hybrid"
            },
            "summary": "Full stack AI engineer experienced in building large-scale vector search pipelines.",
            "languages": [{"language": "English", "proficiency": "Native"}],
            "internships": [{
                "organization": "Aura AI Labs",
                "position": "AI Intern",
                "start_date": "May 2024",
                "end_date": "Aug 2024",
                "description": "Developed vector search RAG microservices."
            }],
            "projects": [{
                "name": "Hiring Intelligence Engine",
                "technologies": "FastAPI, Next.js, PostgreSQL",
                "github_url": "https://github.com/example/hiring-ai"
            }],
            "resume_filename": "cand_resume_2026.pdf",
            "resume_url": "/uploads/resumes/cand_resume_2026.pdf"
        }

        put_resp = await client.put("/api/v1/candidate/profile", json=update_payload, headers=headers)
        assert put_resp.status_code == 200
        updated = put_resp.json()
        assert updated["headline"] == "Senior AI Systems Engineer"
        assert updated["location"] == "San Francisco, CA"
        assert updated["degree"] == "B.Tech / B.E."
        assert updated["college"] == "Indian Institute of Technology (IIT), Bhilai"
        assert len(updated["skills"]) == 4
        assert len(updated["education"]) == 1
        assert updated["career_preferences"]["job_type"] == "Full-time Jobs"

@pytest.mark.asyncio
async def test_candidate_profile_ownership_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create candidate A and candidate B
        cand_a_id = uuid.uuid4()
        cand_b_id = uuid.uuid4()

        async with async_session_factory() as session:
            user_a = User(id=cand_a_id, email=f"user_a_{cand_a_id.hex[:6]}@example.com", password_hash="hash_a", full_name="User A", is_active=True)
            user_b = User(id=cand_b_id, email=f"user_b_{cand_b_id.hex[:6]}@example.com", password_hash="hash_b", full_name="User B", is_active=True)
            session.add_all([user_a, user_b])
            await session.commit()

        token_a = create_access_token(user_id=cand_a_id)
        headers_a = {"Authorization": f"Bearer {token_a}"}

        token_b = create_access_token(user_id=cand_b_id)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A updates profile
        await client.put("/api/v1/candidate/profile", json={"headline": "Headline A"}, headers=headers_a)

        # User B fetches own profile -> receives User B's profile, NOT User A's
        resp_b = await client.get("/api/v1/candidate/profile", headers=headers_b)
        assert resp_b.status_code == 200
        data_b = resp_b.json()
        assert data_b["user_id"] == str(cand_b_id)
        assert data_b["headline"] is None or data_b["headline"] != "Headline A"
