import pytest
import uuid
from datetime import datetime, timedelta, UTC
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from app.db.session import async_session_factory
from app.domains.identity.models import User
from app.main import app

async def _setup_verified_job_and_candidate(client: AsyncClient):
    # Admin User
    admin_email = f"admin_p6_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": admin_email, "password": "Password123!", "full_name": "Admin P6"})
    admin_login = await client.post("/api/v1/auth/login", json={"email": admin_email, "password": "Password123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    async with async_session_factory() as session:
        await session.begin()
        admin_u = (await session.execute(select(User).where(User.email == admin_email))).scalar_one()
        admin_u.is_platform_admin = True
        await session.commit()

    # Recruiter User
    rec_email = f"rec_p6_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": rec_email, "password": "Password123!", "full_name": "Recruiter P6"})
    rec_login = await client.post("/api/v1/auth/login", json={"email": rec_email, "password": "Password123!"})
    rec_headers = {"Authorization": f"Bearer {rec_login.json()['access_token']}"}

    async with async_session_factory() as session:
        rec_u = (await session.execute(select(User).where(User.email == rec_email))).scalar_one()
        rec_user_id = str(rec_u.id)

    org_resp = await client.post("/api/v1/organizations", json={"name": "Workflow Org", "slug": f"wf-org-{uuid.uuid4().hex[:6]}"}, headers=rec_headers)
    org_id = org_resp.json()["id"]
    rec_headers["X-Organization-ID"] = org_id

    job_resp = await client.post("/api/v1/jobs", json={"title": "Senior Staff Architect", "description": "High scale architecture role."}, headers=rec_headers)
    job_id = job_resp.json()["id"]

    await client.post(f"/api/v1/jobs/{job_id}/submit-verification", headers=rec_headers)
    await client.post(f"/api/v1/admin/jobs/{job_id}/verify", json={"action": "APPROVE"}, headers=admin_headers)
    await client.post(f"/api/v1/jobs/{job_id}/publish", headers=rec_headers)

    # Candidate User
    cand_email = f"cand_p6_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/api/v1/auth/register", json={"email": cand_email, "password": "Password123!", "full_name": "Candidate P6"})
    cand_login = await client.post("/api/v1/auth/login", json={"email": cand_email, "password": "Password123!"})
    cand_headers = {"Authorization": f"Bearer {cand_login.json()['access_token']}"}

    app_resp = await client.post("/api/v1/candidate/applications", json={"job_id": job_id, "resume_file_path": "candidates/p6_resume.pdf"}, headers=cand_headers)
    application_id = app_resp.json()["id"]

    return {
        "admin_headers": admin_headers,
        "rec_headers": rec_headers,
        "rec_user_id": rec_user_id,
        "cand_headers": cand_headers,
        "job_id": job_id,
        "application_id": application_id,
    }

@pytest.mark.asyncio
async def test_assessment_creation_assignment_and_completion():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_verified_job_and_candidate(client)

        # 1. Recruiter creates Assessment
        ass_resp = await client.post(f"/api/v1/jobs/{data['job_id']}/assessments", json={"title": "Python System Coding", "duration_minutes": 60, "passing_score": 75}, headers=data["rec_headers"])
        assert ass_resp.status_code == 201
        assessment_id = ass_resp.json()["id"]

        # 2. Recruiter assigns Assessment to Candidate
        assign_resp = await client.post(f"/api/v1/assessments/{assessment_id}/assign", json={"application_id": data["application_id"], "due_days": 7}, headers=data["rec_headers"])
        assert assign_resp.status_code == 201
        assignment_id = assign_resp.json()["id"]
        assert assign_resp.json()["status"] == "SENT"

        # 3. Candidate lists assigned assessments
        cand_list = await client.get("/api/v1/candidate/assessments", headers=data["cand_headers"])
        assert cand_list.status_code == 200
        assert len(cand_list.json()) == 1
        assert cand_list.json()[0]["id"] == assignment_id

        # 4. Candidate completes assessment
        comp_resp = await client.post(f"/api/v1/candidate/assessments/{assignment_id}/submit", headers=data["cand_headers"])
        assert comp_resp.status_code == 200
        assert comp_resp.json()["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_interview_scheduling_and_video_meeting_generation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_verified_job_and_candidate(client)

        start_time = (datetime.now(UTC) + timedelta(days=2)).isoformat()

        # Recruiter schedules Interview
        sched_resp = await client.post("/api/v1/interviews", json={
            "job_id": data["job_id"],
            "application_id": data["application_id"],
            "interviewer_user_id": data["rec_user_id"],
            "interview_type": "TECHNICAL",
            "scheduled_start_at": start_time,
            "duration_minutes": 60,
            "timezone": "America/Chicago",
            "meeting_provider": "TEST",
        }, headers=data["rec_headers"])

        assert sched_resp.status_code == 201
        interview = sched_resp.json()
        assert interview["status"] == "SCHEDULED"
        assert "meeting_url" in interview and interview["meeting_url"] is not None
        assert interview["timezone"] == "America/Chicago"

        # Candidate views scheduled interview
        cand_interviews = await client.get("/api/v1/candidate/interviews", headers=data["cand_headers"])
        assert cand_interviews.status_code == 200
        assert len(cand_interviews.json()) == 1
        assert cand_interviews.json()[0]["id"] == interview["id"]

@pytest.mark.asyncio
async def test_human_email_approval_guard_blocks_unapproved_send():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        data = await _setup_verified_job_and_candidate(client)

        # 1. Draft Email (Status: PENDING_APPROVAL)
        draft_resp = await client.post("/api/v1/communications/draft", json={
            "job_id": data["job_id"],
            "application_id": data["application_id"],
            "workflow_stage": "INTERVIEW_INVITATION",
            "recipient_email": "candidate@example.com",
            "subject": "Invitation to Technical Interview",
            "body": "Dear Candidate, We would like to invite you for a technical interview.",
        }, headers=data["rec_headers"])
        assert draft_resp.status_code == 201
        comm_id = draft_resp.json()["id"]
        assert draft_resp.json()["status"] == "PENDING_APPROVAL"

        # 2. CRITICAL SECURITY GUARD: Attempt to send unapproved email -> MUST return 403 Forbidden
        send_fail = await client.post(f"/api/v1/communications/{comm_id}/send", headers=data["rec_headers"])
        assert send_fail.status_code == 403
        assert "Human Approval Required" in send_fail.json()["detail"]

        # 3. Recruiter explicitly approves email
        appr_resp = await client.post(f"/api/v1/communications/{comm_id}/approve", headers=data["rec_headers"])
        assert appr_resp.status_code == 200
        assert appr_resp.json()["status"] == "APPROVED"

        # 4. Now send succeeds
        send_ok = await client.post(f"/api/v1/communications/{comm_id}/send", headers=data["rec_headers"])
        assert send_ok.status_code == 200
        assert send_ok.json()["status"] == "SENT"
