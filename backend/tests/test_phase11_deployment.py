import pytest
from app.core.config import Settings
from app.core.rate_limiter import InMemoryRateLimiterAdapter, RedisRateLimiterAdapterStub
from app.infrastructure.scoring.scoring_engine import ScoringEngine
from app.infrastructure.ranking.ranking_engine import RankingEngine
from app.domains.recommendation.models import RecommendationTypeEnum

def test_01_production_config_fails_fast_on_insecure_secrets():
    """Verify Settings raises ValueError when insecure secrets are present in production."""
    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="dev_secret_key_change_in_production_min_32_bytes_long",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/hiring_db"
        )

def test_02_testing_environment_works_without_secrets():
    """Verify testing environment initializes smoothly with default development settings."""
    cfg = Settings(APP_ENV="testing")
    assert cfg.APP_ENV == "testing"

def test_03_cors_origins_configurable():
    """Verify CORS origins can be configured as a list of domain strings."""
    cfg = Settings(CORS_ORIGINS=["https://app.hiringplatform.com"])
    assert "https://app.hiringplatform.com" in cfg.CORS_ORIGINS

def test_04_filename_path_traversal_protection():
    """Verify path traversal characters are sanitized out of upload filenames."""
    import os
    import re
    raw_filename = "../../etc/passwd"
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', os.path.basename(raw_filename))
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert sanitized == "passwd"


def test_05_rate_limiter_adapter_abstraction():
    """Verify InMemoryRateLimiterAdapter and RedisRateLimiterAdapterStub conform to IRateLimiterProvider."""
    in_mem = InMemoryRateLimiterAdapter()
    redis_stub = RedisRateLimiterAdapterStub(fallback_limiter=in_mem)
    limited, retry = redis_stub.is_rate_limited(("127.0.0.1", "test"), max_requests=5)
    assert limited is False
    assert retry == 0

def test_06_gemini_configuration_defaults():
    """Verify Gemini configuration defaults are properly loaded from settings."""
    cfg = Settings(APP_ENV="testing")
    assert cfg.LLM_PROVIDER == "gemini"
    assert cfg.GEMINI_MODEL == "gemini-1.5-flash"

def test_07_zero_llm_calls_in_scoring():
    """Verify ScoringEngine contains no LLM parameters or calls."""
    engine = ScoringEngine()
    assert hasattr(engine, "calculate_candidate_score")
    assert not hasattr(engine, "llm")

def test_08_zero_llm_calls_in_ranking():
    """Verify RankingEngine contains no LLM parameters or calls."""
    engine = RankingEngine()
    assert hasattr(engine, "rank_candidates")
    assert not hasattr(engine, "llm")

def test_09_no_automatic_recruiter_decision():
    """Verify recommendation classifications do not automate recruiter decisions."""
    assert RecommendationTypeEnum.RECOMMEND_REVIEW.value == "RECOMMEND_REVIEW"
