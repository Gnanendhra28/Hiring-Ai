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
    """Autouse fixture to clean up synthetic test jobs after test suite execution."""
    yield
    # Post-suite cleanup
    async def run_cleanup():
        async with async_session_factory() as session:
            try:
                await session.execute(text(
                    "DELETE FROM job_intelligence_versions WHERE job_id IN ("
                    "  SELECT j.id FROM jobs j JOIN users u ON j.created_by_user_id = u.id "
                    "  WHERE u.email LIKE '%@example.com' OR u.email LIKE '%@p9d.com' OR u.email LIKE '%@test.com' OR u.email LIKE '%@company.com' OR u.email LIKE 'rec_%' OR u.email LIKE 'user_%' OR u.email LIKE 'emp_%' OR u.email LIKE 'cand_%' OR u.email LIKE 'phase%' OR u.email LIKE 'test_%'"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM applications WHERE job_id IN ("
                    "  SELECT j.id FROM jobs j JOIN users u ON j.created_by_user_id = u.id "
                    "  WHERE u.email LIKE '%@example.com' OR u.email LIKE '%@p9d.com' OR u.email LIKE '%@test.com' OR u.email LIKE '%@company.com' OR u.email LIKE 'rec_%' OR u.email LIKE 'user_%' OR u.email LIKE 'emp_%' OR u.email LIKE 'cand_%' OR u.email LIKE 'phase%' OR u.email LIKE 'test_%'"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM jobs WHERE created_by_user_id IN ("
                    "  SELECT id FROM users "
                    "  WHERE email LIKE '%@example.com' OR email LIKE '%@p9d.com' OR email LIKE '%@test.com' OR email LIKE '%@company.com' OR email LIKE 'rec_%' OR email LIKE 'user_%' OR email LIKE 'emp_%' OR email LIKE 'cand_%' OR email LIKE 'phase%' OR email LIKE 'test_%'"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM organization_memberships WHERE user_id IN ("
                    "  SELECT id FROM users "
                    "  WHERE email LIKE '%@example.com' OR email LIKE '%@p9d.com' OR email LIKE '%@test.com' OR email LIKE '%@company.com' OR email LIKE 'rec_%' OR email LIKE 'user_%' OR email LIKE 'emp_%' OR email LIKE 'cand_%' OR email LIKE 'phase%' OR email LIKE 'test_%'"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM audit_logs WHERE user_id IN ("
                    "  SELECT id FROM users "
                    "  WHERE email LIKE '%@example.com' OR email LIKE '%@p9d.com' OR email LIKE '%@test.com' OR email LIKE '%@company.com' OR email LIKE 'rec_%' OR email LIKE 'user_%' OR email LIKE 'emp_%' OR email LIKE 'cand_%' OR email LIKE 'phase%' OR email LIKE 'test_%'"
                    ");"
                ))
                await session.execute(text(
                    "DELETE FROM users "
                    "WHERE email LIKE '%@example.com' OR email LIKE '%@p9d.com' OR email LIKE '%@test.com' OR email LIKE '%@company.com' OR email LIKE 'rec_%' OR email LIKE 'user_%' OR email LIKE 'emp_%' OR email LIKE 'cand_%' OR email LIKE 'phase%' OR email LIKE 'test_%';"
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
