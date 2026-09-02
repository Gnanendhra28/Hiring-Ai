import pytest
from app.infrastructure.parsing.semantic_extractor import SemanticJobExtractor
from app.infrastructure.validation.job_intelligence_validator import JobIntelligenceValidator
from app.domains.jobs.models import Job
from app.db.session import async_session_factory
from sqlalchemy import select

REAL_ML_ENGINEER_TEXT = """
## About the Company
AuraHire AI is an enterprise talent intelligence platform powering automated candidate matching.

## Work Location & Schedule
- Location: Hyderabad, Telangana (Remote)

## Key Responsibilities
• Develop and productionize machine learning models for real-world business problems
• Perform data preprocessing, feature engineering, and model evaluation
• Train and optimize classification, regression, and ranking models
• Design reusable ML pipelines for training and inference
• Monitor model performance and identify model drift
• Collaborate with data engineers and software engineers to deploy ML solutions

## Required Key Skills
- Python
- Machine Learning
- Scikit-learn
- Pandas
- NumPy
- SQL

## Preferred Qualifications & Skills
- XGBoost
- LightGBM
- PyTorch
- MLflow
- Docker

## Good to Have Knowledge
- Kubernetes
- AWS
- Airflow
- Spark
- PostgreSQL
"""

UNHEADED_PARAGRAPH_TEXT = """
We are looking for a Machine Learning Engineer. You will develop and deploy ML models using Python and TensorFlow.
Strong knowledge of machine learning and scikit-learn is required. NLP experience is preferred. Knowledge of Docker is a plus.
"""

def test_semantic_extraction_for_real_ml_engineer_job():
    res = SemanticJobExtractor.extract_semantic_intelligence(REAL_ML_ENGINEER_TEXT, "Machine Learning Engineer")

    reqs = res["requirements"]
    resps = res["responsibilities"]

    required_skills = [r["canonical_value"] for r in reqs if r["requirement_level"] == "REQUIRED"]
    preferred_skills = [r["canonical_value"] for r in reqs if r["requirement_level"] == "PREFERRED"]
    good_to_have_skills = [r["canonical_value"] for r in reqs if r["requirement_level"] == "NICE_TO_HAVE"]

    assert "Python" in required_skills
    assert "Machine Learning" in required_skills
    assert "Scikit-learn" in required_skills
    assert "SQL" in required_skills

    assert "XGBoost" in preferred_skills
    assert "PyTorch" in preferred_skills
    assert "Docker" in preferred_skills

    assert "Kubernetes" in good_to_have_skills
    assert "AWS" in good_to_have_skills
    assert "PostgreSQL" in good_to_have_skills

    assert len(resps) >= 5
    assert any("productionize machine learning models" in r for r in resps)

def test_semantic_extraction_for_unheaded_paragraph_text():
    res = SemanticJobExtractor.extract_semantic_intelligence(UNHEADED_PARAGRAPH_TEXT, "Machine Learning Engineer")

    reqs = res["requirements"]

    validated_report = JobIntelligenceValidator.validate_and_filter_requirements(
        raw_text=UNHEADED_PARAGRAPH_TEXT,
        requirements=reqs,
    )

    validated_reqs = validated_report["validated_requirements"]
    canon_names = [r["canonical_value"] for r in validated_reqs]

    assert "Python" in canon_names
    assert "TensorFlow" in canon_names
    assert "Machine Learning" in canon_names

@pytest.mark.asyncio
async def test_real_db_machine_learning_engineer_job_extraction():
    async with async_session_factory() as session:
        stmt = select(Job).where(Job.title == "Machine Learning Engineer")
        job = (await session.execute(stmt)).scalars().first()
        assert job is not None, "Real DB Machine Learning Engineer job must exist"

        res = SemanticJobExtractor.extract_semantic_intelligence(job.description, job.title)
        assert len(res["requirements"]) > 0, "Requirements must be extracted from real DB job description"
        assert len(res["responsibilities"]) > 0, "Responsibilities must be extracted from real DB job description"
