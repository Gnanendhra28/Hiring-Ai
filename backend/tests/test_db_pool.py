import pytest
from app.core.config import settings

def test_database_pool_configuration():
    # Verify defaults are tuned to safe production limits (pool size <= 10, max overflow <= 10)
    assert settings.DATABASE_POOL_SIZE <= 10
    assert settings.DATABASE_MAX_OVERFLOW <= 10

