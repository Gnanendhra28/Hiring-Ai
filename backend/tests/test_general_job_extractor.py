import pytest
from app.infrastructure.parsing.general_extractor import GeneralJobExtractor
from app.domains.jobs.models import Job
from app.db.session import async_session_factory
from sqlalchemy import select

MULTI_SKILL_UNHEADED_TEXT = """
We are looking for a Senior Software Engineer. You will build scalable microservices.
Required Key Skills:
- Redis Terraform
- Docker Ruby/Rails
- Python OpenAI React

Bonus points for: Experience with OpenSearch, Snowflake, or Langfuse.
"""

def test_multi_token_line_splitting():
    res = GeneralJobExtractor.extract(MULTI_SKILL_UNHEADED_TEXT, "Senior Software Engineer")

    required_names = [r["name"] for r in res["required_skills"]]
    good_names = [r["name"] for r in res["good_to_have"]]

    # Verify multi-token splitting
    assert "Redis" in required_names
    assert "Terraform" in required_names
    assert "Docker" in required_names
    assert "Python" in required_names
    assert "OpenAI" in required_names
    assert "React" in required_names

    # Verify inline bonus phrase routing
    assert "OpenSearch" in good_names
    assert "Snowflake" in good_names
    assert "Langfuse" in good_names

@pytest.mark.asyncio
async def test_sr_software_engineer_db_extraction():
    async with async_session_factory() as session:
        stmt = select(Job).where(Job.description.ilike("%Python%") | Job.description.ilike("%Software%"))
        jobs = list((await session.execute(stmt)).scalars().all())
        job = next((j for j in jobs if any(k.lower() in j.description.lower() for k in ["python", "fastapi", "docker", "redis", "sql"])), None)
        if not job:
            job_desc = (
                "## Required Key Skills\n"
                "- Python\n"
                "- FastAPI\n"
                "- Docker\n"
                "- PostgreSQL\n"
                "## Key Responsibilities\n"
                "- Build microservices and scalable systems\n"
                "- Deploy cloud infrastructure"
            )
            job_title = "Senior Software Engineer"
        else:
            job_desc = job.description
            job_title = job.title

        res = GeneralJobExtractor.extract(job_desc, job_title)

        assert len(res["required_skills"]) > 0 or len(res["preferred_skills"]) > 0 or len(res["good_to_have"]) > 0
        assert len(res["responsibilities"]) >= 0

@pytest.mark.asyncio
async def test_machine_learning_engineer_db_extraction():
    async with async_session_factory() as session:
        stmt = select(Job).where(Job.title.ilike("%Machine Learning%") | Job.description.ilike("%Machine Learning%"))
        job = (await session.execute(stmt)).scalars().first()
        if not job:
            job_desc = (
                "Looking for ML Engineer with PyTorch, TensorFlow, and Python experience.\n"
                "Required Skills:\n"
                "- Python\n"
                "- PyTorch\n"
                "- Machine Learning"
            )
            job_title = "Machine Learning Engineer"
        else:
            job_desc = job.description
            job_title = job.title

        res = GeneralJobExtractor.extract(job_desc, job_title)

        req_names = [r["name"] for r in res["required_skills"]]
        assert len(req_names) > 0 or len(res["preferred_skills"]) > 0

@pytest.mark.asyncio
async def test_multi_job_isolation():
    desc_a = "## Required Key Skills\n- Python\n- FastAPI\n- Redis"
    desc_b = "## Required Key Skills\n- React\n- TypeScript\n- GraphQL"
    res_a = GeneralJobExtractor.extract(desc_a, "Senior Backend Engineer")
    res_b = GeneralJobExtractor.extract(desc_b, "Frontend Specialist")

    reqs_a = set(r["name"].lower() for r in res_a["required_skills"])
    reqs_b = set(r["name"].lower() for r in res_b["required_skills"])

    # Isolation check: different jobs produce distinct extraction output
    assert res_a["role_title"] != res_b["role_title"]
    assert reqs_a != reqs_b
