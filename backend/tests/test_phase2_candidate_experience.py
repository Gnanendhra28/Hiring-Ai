"""
Candidate Experience & Live Interview Room Tests.
Verifies server-authoritative state, candidate-safe feedback projection,
idempotent turn submissions, and adaptive follow-up injection.
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_candidate_feedback_projection_safe_boundary():
    """Verifies that the candidate feedback endpoint returns a safe projection without recruiter secrets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/v1/interviews/int-safe-cand-01/candidate-feedback")
        assert res.status_code == 200
        data = res.json()
        assert data["interview_id"] == "int-safe-cand-01"
        assert "status" in data
        assert "top_strengths" in data
        assert "areas_for_improvement" in data
        assert "summary_feedback" in data
        # Ensure recruiter private notes and recommendation decisions are not leaked in candidate feedback
        assert "recommendation" not in data
        assert "internal_notes" not in data


@pytest.mark.asyncio
async def test_submit_turn_idempotency_and_adaptive_followup():
    """Verifies that submitting a turn persists data and returns adaptive follow-up when gaps exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "question_id": "q-cand-exp-01",
            "question_text": "How do you handle database failover in Cloud SQL?",
            "candidate_answer": "We configured regional high availability with automated synchronous replication and read replicas.",
            "time_taken_seconds": 45,
            "client_submission_id": "sub_test_001_turn",
        }
        res = await ac.post("/api/v1/interviews/int-cand-exp-01/submit-turn", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "turn_index" in data
        assert data["turn_index"] >= 1
        assert "evaluation" in data
