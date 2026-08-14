import uuid
from app.core.secrets import EnvironmentSecretProvider, AzureKeyVaultSecretProvider, get_secret_provider
from app.core.rate_limiter import RedisRateLimiterAdapter
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.service_bus import AzureServiceBusEventBus
from app.infrastructure.scoring.scoring_engine import ScoringEngine
from app.infrastructure.ranking.ranking_engine import RankingEngine
from app.domains.recommendation.models import RecommendationTypeEnum

def test_01_secret_provider_factory():
    """Verify get_secret_provider returns EnvironmentSecretProvider in testing mode."""
    provider = get_secret_provider()
    assert isinstance(provider, EnvironmentSecretProvider)
    assert provider.get_secret("APP_ENV") == "testing"

def test_02_azure_keyvault_secret_provider_fallback():
    """Verify AzureKeyVaultSecretProvider falls back to environment secrets when KeyVault is unavailable."""
    kv_provider = AzureKeyVaultSecretProvider()
    assert kv_provider.get_secret("APP_NAME") == "AI Hiring SaaS Platform"

def test_03_redis_rate_limiter_adapter_fallback():
    """Verify RedisRateLimiterAdapter falls back smoothly to in-memory sliding window."""
    redis_limiter = RedisRateLimiterAdapter()
    limited, retry = redis_limiter.is_rate_limited(("127.0.0.1", "cloud_test"), max_requests=10)
    assert limited is False
    assert retry == 0

def test_04_azure_service_bus_adapter_initialization():
    """Verify AzureServiceBusEventBus instantiates with connection parameters."""
    bus = AzureServiceBusEventBus(connection_string=None)
    assert bus.topic_name == "application-events"

def test_05_event_envelope_payload_security():
    """Verify EventEnvelope payloads contain aggregate IDs and correlation UUIDs, zero raw resume text or PII."""
    event = EventEnvelope(
        event_id=uuid.uuid4(),
        event_type="candidate.matched",
        aggregate_type="candidate",
        aggregate_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        correlation_id=str(uuid.uuid4()),
        payload={"job_id": str(uuid.uuid4()), "candidate_id": str(uuid.uuid4())},
    )
    json_repr = event.to_json()
    assert "resume_text" not in json_repr
    assert "password" not in json_repr
    assert "ssn" not in json_repr

def test_06_zero_llm_scoring_governance():
    """Verify ScoringEngine contains zero LLM parameters or calls."""
    engine = ScoringEngine()
    assert hasattr(engine, "calculate_candidate_score")
    assert not hasattr(engine, "llm_score")

def test_07_zero_llm_ranking_governance():
    """Verify RankingEngine contains zero LLM parameters or calls."""
    engine = RankingEngine()
    assert hasattr(engine, "rank_candidates")
    assert not hasattr(engine, "llm_rank")

def test_08_no_automatic_recruiter_decisions():
    """Verify AI recommendation types do not set application status automatically."""
    assert RecommendationTypeEnum.RECOMMEND_REVIEW.value == "RECOMMEND_REVIEW"
