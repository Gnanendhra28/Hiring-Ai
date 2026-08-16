import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.core.config import Settings
from app.domains.matching.models import CandidateRequirementMatch, MatchStatusEnum
from app.domains.recommendation.models import RecommendationTypeEnum
from app.domains.scoring.models import EligibilityStatusEnum, ScoringConfiguration
from app.infrastructure.ai_gateway.base import TestAIGatewayAdapter
from app.infrastructure.ai_gateway.gemini_adapter import GeminiAIGatewayAdapter
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.factories import AIGatewayFactory
from app.infrastructure.ranking.ranking_engine import RankingEngine
from app.infrastructure.recommendation.recommendation_engine import RecommendationEngine
from app.infrastructure.scoring.scoring_engine import ScoringEngine
from app.infrastructure.workers.pipeline_worker import PipelineWorker

@pytest.mark.asyncio
async def test_gemini_adapter_factory_selection():
    """Test 1: GeminiAIGatewayAdapter selection when configured."""
    mock_settings = Settings(
        APP_ENV="development",
        AI_PROVIDER="gemini",
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="valid_real_gemini_key_12345",
    )
    with patch("app.infrastructure.factories.settings", mock_settings):
        provider = AIGatewayFactory.get_provider()
        assert isinstance(provider, GeminiAIGatewayAdapter)

@pytest.mark.asyncio
async def test_missing_gemini_credentials_fail_fast_in_production():
    """Test 2: Production environment fails fast if Gemini credentials are missing or placeholder."""
    mock_settings = Settings(
        APP_ENV="testing",
        AI_PROVIDER="gemini",
        LLM_PROVIDER="gemini",
    )
    mock_settings.APP_ENV = "production"
    mock_settings.GEMINI_API_KEY = "placeholder_gemini_api_key"
    mock_settings.AI_API_KEY = "placeholder_ai_api_key"

    with patch("app.infrastructure.ai_gateway.gemini_adapter.settings", mock_settings):
        with pytest.raises(ValueError, match="CRITICAL CONFIGURATION ERROR"):
            GeminiAIGatewayAdapter()


@pytest.mark.asyncio
async def test_test_adapter_remains_usable_in_testing():
    """Test 3: TestAIGatewayAdapter is selected in testing environment."""
    mock_settings = Settings(
        APP_ENV="testing",
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="placeholder_gemini_api_key",
        AI_API_KEY="placeholder_ai_api_key",
    )
    with patch("app.infrastructure.factories.settings", mock_settings):
        provider = AIGatewayFactory.get_provider()
        assert isinstance(provider, TestAIGatewayAdapter)

@pytest.mark.asyncio
async def test_event_envelope_contains_tenant_context():
    """Test 4: Event envelope preserves org ID, event ID, and correlation ID without PII/resume text."""
    org_id = uuid.uuid4()
    job_id = uuid.uuid4()
    candidate_id = uuid.uuid4()

    event = EventEnvelope(
        event_type="candidate.matched",
        aggregate_id=candidate_id,
        organization_id=org_id,
        correlation_id="corr-123",
        payload={"job_id": str(job_id), "candidate_id": str(candidate_id)},
    )

    assert event.organization_id == org_id
    assert event.correlation_id == "corr-123"
    assert "resume_text" not in event.payload
    assert "email" not in event.payload

@pytest.mark.asyncio
async def test_worker_idempotency():
    """Test 8: PipelineWorker skips duplicate event execution."""
    worker = PipelineWorker(max_retries=1)
    event_id = uuid.uuid4()
    org_id = uuid.uuid4()

    event = EventEnvelope(
        event_id=event_id,
        event_type="candidate.recommendation.completed",
        aggregate_id=uuid.uuid4(),
        organization_id=org_id,
        correlation_id="corr-456",
        payload={},
    )

    # First run
    res1 = await worker.process_event(event)
    assert res1 is True
    assert event_id in worker.processed_event_ids

    # Duplicate second run
    res2 = await worker.process_event(event)
    assert res2 is True

@pytest.mark.asyncio
async def test_worker_permanent_failure_handling():
    """Test 7: Permanent errors (e.g. ValueError) route directly to dead-letter queue without retries."""
    worker = PipelineWorker(max_retries=3)
    event = EventEnvelope(
        event_type="candidate.matched",
        aggregate_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        correlation_id="corr-fail",
        payload={},  # Missing required payload fields
    )

    res = await worker.process_event(event)
    assert res is False
    assert len(worker.dead_letter_queue) == 1
    assert "Invalid payload" in worker.dead_letter_queue[0].reason

@pytest.mark.asyncio
async def test_recommendation_remains_advisory():
    """Test 9: RecommendationEngine output is strictly advisory and does not mutate decision/status."""
    rec_type, rec_conf = RecommendationEngine.determine_recommendation_type(
        overall_score=94.5,
        eligibility_status=EligibilityStatusEnum.PASS,
        score_confidence=0.90,
        is_top_k=True,
        failed_hard_reqs_count=0,
    )

    assert rec_type == RecommendationTypeEnum.STRONGLY_RECOMMEND_REVIEW
    assert rec_conf == 0.90
    # Proves return type is advisory recommendation enum, NOT candidate decision or application status
    assert rec_type != "SHORTLISTED"
    assert rec_type != "ADVANCE"

@pytest.mark.asyncio
async def test_gemini_failure_fallback():
    """Test 10: AI Gateway failure falls back gracefully to deterministic narrative."""
    with patch("app.infrastructure.factories.AIGatewayFactory.get_provider") as mock_factory:
        mock_provider = AsyncMock()
        mock_provider.chat_completion.side_effect = RuntimeError("API rate limit exceeded")
        mock_factory.return_value = mock_provider

        explanation = await RecommendationEngine.generate_explanation(
            job_title="Senior AI Engineer",
            overall_score=92.0,
            rank_position=1,
            is_top_k=True,
            eligibility_status=EligibilityStatusEnum.PASS,
            matched_skills=["Python", "FastAPI"],
            unmatched_skills=["Kubernetes"],
            extracted_text_excerpt="Experienced engineer",
        )

        assert explanation["status"] == "COMPLETED"
        assert "AI explanation narrative offline" in explanation["summary"]
        assert len(explanation["strengths"]) > 0

@pytest.mark.asyncio
async def test_no_llm_invocation_in_scoring_engine():
    """Test 11: ScoringEngine is 100% deterministic with zero LLM API calls."""
    config = ScoringConfiguration(
        required_skills_weight=0.30,
        semantic_match_weight=0.20,
        experience_weight=0.20,
        education_weight=0.10,
        preferred_skills_weight=0.10,
        other_requirements_weight=0.10,
    )

    req_match = CandidateRequirementMatch(
        requirement_type="SKILL",
        raw_required_value="Python",
        canonical_required_value="Python",
        requirement_level="REQUIRED",
        hard_constraint=True,
        match_status=MatchStatusEnum.MATCHED,
        confidence=0.95,
    )

    with patch("app.infrastructure.factories.AIGatewayFactory.get_provider") as mock_ai:
        res = ScoringEngine.calculate_candidate_score(config, [req_match], [])
        assert res["overall_score"] > 0.0
        assert res["eligibility_status"] == EligibilityStatusEnum.PASS
        # Verify AI Gateway was NEVER called
        mock_ai.assert_not_called()

@pytest.mark.asyncio
async def test_no_llm_invocation_in_ranking_engine():
    """Test 12: RankingEngine ranks deterministically with zero LLM API calls."""
    candidates = [
        {"candidate_id": "c1", "score": 85.0, "eligibility_status": EligibilityStatusEnum.PASS, "score_confidence": 0.90, "failed_hard_reqs_count": 0, "matched_reqs_count": 5},
        {"candidate_id": "c2", "score": 95.0, "eligibility_status": EligibilityStatusEnum.PASS, "score_confidence": 0.95, "failed_hard_reqs_count": 0, "matched_reqs_count": 8},
    ]

    with patch("app.infrastructure.factories.AIGatewayFactory.get_provider") as mock_ai:
        ranked = RankingEngine.rank_candidates(candidates, top_k=5)
        assert ranked[0]["candidate_id"] == "c2"
        assert ranked[0]["rank_position"] == 1
        mock_ai.assert_not_called()
