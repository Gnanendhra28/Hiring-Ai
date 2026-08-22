import pytest
import asyncio
from app.db.session import async_session_factory
from sqlalchemy import text

REAL_JOB_TITLES = {
    "Generative AI Engineer",
    "Backend Engineer – Python",
    "Machine Learning Engineer",
    "AI/ML Engineer – RAG",
}

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_jobs_after_suite():
    """Autouse fixture to clean up lingering test jobs after test suite execution."""
    yield
    # Post-suite cleanup
    async def run_cleanup():
        async with async_session_factory() as session:
            try:
                await session.execute(text(
                    "DELETE FROM job_intelligence_versions WHERE job_id IN ("
                    "  SELECT id FROM jobs WHERE title NOT IN ('Generative AI Engineer', 'Backend Engineer – Python', 'Machine Learning Engineer', 'AI/ML Engineer – RAG')"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM applications WHERE job_id IN ("
                    "  SELECT id FROM jobs WHERE title NOT IN ('Generative AI Engineer', 'Backend Engineer – Python', 'Machine Learning Engineer', 'AI/ML Engineer – RAG')"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM jobs WHERE title NOT IN ('Generative AI Engineer', 'Backend Engineer – Python', 'Machine Learning Engineer', 'AI/ML Engineer – RAG');"
                ))
                await session.commit()
            except Exception as e:
                print(f"[TEST CLEANUP ERROR] {e}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run_cleanup())
        else:
            loop.run_until_complete(run_cleanup())
    except Exception:
        asyncio.run(run_cleanup())
