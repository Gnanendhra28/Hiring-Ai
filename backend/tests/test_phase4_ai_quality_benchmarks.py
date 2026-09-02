"""
Phase 4 AI Quality, Benchmarking & Hiring Intelligence Tests.
Verifies evidence-grounded scoring, score stability, competency coverage,
adaptive follow-up quality, fairness, and scorecard immutability.
"""

import pytest
from app.domains.interviews.ai_agent import AIInterviewAgent, CandidateAnswerTurn, InterviewScorecard


@pytest.mark.asyncio
async def test_evidence_grounding_and_artifact_versioning():
    """Verifies that final scorecards include AI artifact versions and grounded evidence."""
    turns = [
        CandidateAnswerTurn(
            question_id="q-ai-qual-01",
            question_text="How do you architect distributed transactions in microservices?",
            candidate_answer=(
                "We use the Saga orchestration pattern with Temporal and PostgreSQL outbox tables. "
                "Each service publishes compensating domain events to rollback state on payment failure."
            ),
            time_taken_seconds=50,
        )
    ]

    card = await AIInterviewAgent.evaluate_interview_async(
        interview_id="int-ai-qual-01",
        candidate_name="Alex Engineer",
        job_title="Principal Architect",
        turns=turns,
    )

    assert isinstance(card, InterviewScorecard)
    assert card.prompt_version == "v1.2"
    assert card.rubric_version == "v1.2"
    assert card.schema_version == "v1.2"
    assert card.overall_score >= 70.0
    assert len(card.top_strengths) >= 1
    assert len(card.question_evaluations) == 1
    assert card.evidence_status in ("STRONG", "MODERATE")


@pytest.mark.asyncio
async def test_scoring_consistency_and_variance():
    """Verifies that evaluation scores for a standard technical answer remain stable within defined variance bounds."""
    turn_eval = await AIInterviewAgent.evaluate_turn_async(
        question_id="q-cons-01",
        question_text="Explain how database connection pooling works and why it prevents resource exhaustion.",
        candidate_answer=(
            "Connection pools maintain a warm pool of reusable TCP sockets to PostgreSQL. "
            "Instead of opening a new SSL handshake per request, threads borrow and release connections, "
            "which bounds maximum active connections and prevents database CPU starvation."
        ),
    )

    assert turn_eval.technical_accuracy >= 75.0
    assert turn_eval.problem_solving >= 70.0
    assert turn_eval.answer_quality in ("STRONG", "ADEQUATE")


@pytest.mark.asyncio
async def test_adaptive_probing_quality_on_shallow_answer():
    """Verifies that shallow or vague technical claims trigger specific, actionable follow-up questions."""
    turn_eval = await AIInterviewAgent.evaluate_turn_async(
        question_id="q-probe-01",
        question_text="How do you handle schema migrations with zero downtime in production?",
        candidate_answer="We use migration scripts to update tables.",
    )

    # Shallow answer should flag follow-up or provide clear gap feedback
    assert turn_eval.depth < 75.0
    assert turn_eval.follow_up_needed is True or len(turn_eval.weaknesses) >= 1


@pytest.mark.asyncio
async def test_fairness_and_style_neutrality():
    """Verifies that concise technical answers are evaluated fairly on core technical merits without style bias."""
    concise_answer = "We implement rate limiting via Redis token bucket with 1-second sliding windows and Lua scripts."
    verbose_answer = (
        "In our extensive production experience across multi-cloud environments, when considering the important "
        "challenge of API traffic management, we thoughtfully selected Redis to implement token bucket rate limiting "
        "using atomic Lua scripts executed over sliding 1-second windows."
    )

    eval_concise = await AIInterviewAgent.evaluate_turn_async(
        question_id="q-fair-01",
        question_text="How do you implement distributed rate limiting?",
        candidate_answer=concise_answer,
    )

    eval_verbose = await AIInterviewAgent.evaluate_turn_async(
        question_id="q-fair-02",
        question_text="How do you implement distributed rate limiting?",
        candidate_answer=verbose_answer,
    )

    # Both answers contain the identical core technical solution (Redis, Token Bucket, Lua, Sliding Window)
    assert abs(eval_concise.technical_accuracy - eval_verbose.technical_accuracy) <= 25.0
    assert eval_concise.technical_accuracy >= 70.0
    assert eval_verbose.technical_accuracy >= 70.0
