"""
Test Suite for Phase 2: Firebase Authentication & Firestore Production State.
Verifies Firebase ID token verification, Firestore turn persistence, scorecard persistence,
restart statelessness, and tenant isolation.
"""

import pytest
import shutil
from pathlib import Path
from app.domains.interviews.ai_agent import (
    CandidateAnswerTurn,
    InterviewScorecard,
    QuestionEvaluation,
    TurnEvaluation,
)
from app.infrastructure.firebase.auth import FirebaseAuthService
from app.infrastructure.firestore.interview_repo import FirestoreInterviewRepository


@pytest.fixture
def temp_firestore_repo(tmp_path):
    """Provides an isolated Firestore repository directory for testing."""
    repo = FirestoreInterviewRepository(storage_dir=str(tmp_path / "firestore_test"))
    yield repo
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.mark.asyncio
async def test_firebase_token_verifier_invalid_token():
    """Verifies that malformed or empty Firebase ID tokens are rejected."""
    res = await FirebaseAuthService.verify_id_token("invalid_token_xyz")
    assert res is None


@pytest.mark.asyncio
async def test_firestore_turn_persistence(temp_firestore_repo):
    """Verifies candidate turns and evaluations are written and read from persistent Firestore documents."""
    interview_id = "int-test-firestore-001"
    turn1 = CandidateAnswerTurn(
        question_id="q-1",
        question_text="Explain asyncpg connection pool optimization.",
        candidate_answer="We configured asyncpg with max_size=20, min_size=5, and command timeouts to eliminate pool exhaustion.",
        time_taken_seconds=45,
    )
    turn_eval = TurnEvaluation(
        question_id="q-1",
        technical_accuracy=90.0,
        depth=85.0,
        clarity=92.0,
        problem_solving=88.0,
        strengths=["Clear practical knowledge of asyncpg pool sizing"],
        answer_quality="STRONG",
        follow_up_needed=False,
    )

    await temp_firestore_repo.save_turn(interview_id, turn1, turn_eval)

    # Retrieve turns
    turns = await temp_firestore_repo.get_turns(interview_id)
    assert len(turns) == 1
    assert turns[0].question_id == "q-1"
    assert "asyncpg" in turns[0].candidate_answer


@pytest.mark.asyncio
async def test_firestore_restart_statelessness(tmp_path):
    """Verifies that when a container restarts (new repository instance), interview state is preserved."""
    storage_dir = str(tmp_path / "firestore_restart_test")
    interview_id = "int-restart-002"

    # Container Instance 1
    instance_1 = FirestoreInterviewRepository(storage_dir=storage_dir)
    turn = CandidateAnswerTurn(
        question_id="q-sys",
        question_text="Design a distributed cache.",
        candidate_answer="We deployed Redis cluster with sentinel failover.",
    )
    await instance_1.save_turn(interview_id, turn)

    # Container Instance 2 (Simulating Cloud Run cold-start or scale out)
    instance_2 = FirestoreInterviewRepository(storage_dir=storage_dir)
    loaded_turns = await instance_2.get_turns(interview_id)

    assert len(loaded_turns) == 1
    assert loaded_turns[0].question_id == "q-sys"
    assert loaded_turns[0].candidate_answer == turn.candidate_answer


@pytest.mark.asyncio
async def test_firestore_scorecard_persistence(temp_firestore_repo):
    """Verifies that final scorecards persist and can be retrieved across sessions."""
    interview_id = "int-scorecard-003"
    scorecard = InterviewScorecard(
        interview_id=interview_id,
        candidate_name="Sarah Connor",
        job_title="Principal AI Architect",
        overall_score=94.5,
        recommendation="STRONG_HIRE",
        technical_depth_score=96.0,
        problem_solving_score=92.0,
        system_design_score=95.0,
        communication_score=95.0,
        summary="Candidate showed mastery in distributed AI architectures.",
        top_strengths=["Distributed systems", "RAG vector retrieval at scale"],
        areas_for_improvement=[],
        skill_gaps=[],
        recommendation_reason="Scored 94.5/100 with comprehensive responses.",
    )

    await temp_firestore_repo.save_scorecard(interview_id, scorecard)

    loaded_card = await temp_firestore_repo.get_scorecard(interview_id)
    assert loaded_card is not None
    assert loaded_card.candidate_name == "Sarah Connor"
    assert loaded_card.overall_score == 94.5
    assert loaded_card.recommendation == "STRONG_HIRE"


@pytest.mark.asyncio
async def test_interview_session_isolation(temp_firestore_repo):
    """Verifies that separate interview sessions do not leak data across documents."""
    await temp_firestore_repo.save_turn(
        "int-user-A",
        CandidateAnswerTurn(question_id="q-1", question_text="Q1", candidate_answer="User A answer"),
    )
    await temp_firestore_repo.save_turn(
        "int-user-B",
        CandidateAnswerTurn(question_id="q-1", question_text="Q1", candidate_answer="User B answer"),
    )

    turns_a = await temp_firestore_repo.get_turns("int-user-A")
    turns_b = await temp_firestore_repo.get_turns("int-user-B")

    assert len(turns_a) == 1
    assert len(turns_b) == 1
    assert turns_a[0].candidate_answer == "User A answer"
    assert turns_b[0].candidate_answer == "User B answer"
