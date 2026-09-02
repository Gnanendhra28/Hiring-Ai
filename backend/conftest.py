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
def initialize_test_database_schema():
    """Ensures database tables and schema columns are created before tests execute."""
    async def run_setup():
        from app.db.base import Base
        from app.db.session import engine
        import app.domains.identity.models
        import app.domains.organizations.models
        import app.domains.jobs.models
        import app.domains.candidates.models
        import app.domains.applications.models
        import app.domains.interviews.models
        import app.domains.audit.models
        import app.domains.recommendation.models
        import app.domains.document_intelligence.models
        import app.domains.recruiters.models  # noqa: F401

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                schema_ddl = [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);",
                    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary VARCHAR(100);",
                    "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_website VARCHAR(500);",
                    "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS resume_url VARCHAR(1024);",
                    "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS raw_resume_text TEXT;",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS registration_id VARCHAR(255);",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500);",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) NOT NULL DEFAULT 'UNVERIFIED';",
                    "ALTER TABLE recruiter_profiles ADD COLUMN IF NOT EXISTS submitted_at VARCHAR(100);",
                ]
                for ddl in schema_ddl:
                    try:
                        await conn.execute(text(ddl))
                    except Exception:
                        pass
        except Exception as e:
            print(f"[TEST SCHEMA INIT WARNING] {e!s}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run_setup())
        else:
            loop.run_until_complete(run_setup())
    except RuntimeError:
        asyncio.run(run_setup())

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
                print(f"[TEST CLEANUP ERROR] {e!s}")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(run_cleanup())
        else:
            loop.run_until_complete(run_cleanup())
    except RuntimeError:
        asyncio.run(run_cleanup())
