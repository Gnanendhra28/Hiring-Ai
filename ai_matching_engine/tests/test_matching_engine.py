"""
Test Suite for 3-Tier AI Recruitment Matching Engine
"""

import pytest
from ai_matching_engine.models import (
    CandidateProfile,
    EducationItem,
    JobDescription,
    LLMEvaluationOutput,
    ProjectItem,
    TierScoreResult,
    WorkExperienceItem,
)
from ai_matching_engine.tier1_vector import VectorSearchEngine
from ai_matching_engine.tier2_rerank import CrossEncoderReranker
from ai_matching_engine.tier3_llm import LLMEvaluator
from ai_matching_engine.main import RecruitmentMatchingEngine


@pytest.fixture
def sample_jd():
    return JobDescription(
        id="jd-python-lead",
        title="Lead Python Backend Engineer",
        department="Platform Engineering",
        required_skills=["Python", "FastAPI", "PostgreSQL", "System Design"],
        preferred_skills=["Docker", "Kubernetes", "Redis"],
        experience_required_years=5.0,
        responsibilities=[
            "Design scalable microservices using FastAPI",
            "Optimize PostgreSQL database queries and connection pools",
        ],
        description="Looking for an experienced Lead Python Engineer with expertise in FastAPI, microservices, and database tuning.",
    )


@pytest.fixture
def sample_strong_candidate():
    return CandidateProfile(
        id="cand-senior",
        name="Sarah Connor",
        headline="Senior Backend Engineer & Architect",
        summary="6+ years building high-load distributed Python systems with FastAPI and PostgreSQL.",
        skills=["Python", "FastAPI", "PostgreSQL", "System Design", "Docker", "Redis", "Git"],
        experience_years=6.0,
        work_history=[
            WorkExperienceItem(
                title="Senior Software Engineer",
                company="TechCorp",
                duration_years=4.0,
                description="Engineered FastAPI microservices and PostgreSQL database schemas.",
            )
        ],
        projects=[
            ProjectItem(
                name="Distributed Task Pipeline",
                description="Built high-throughput message processing pipeline using Python and Redis.",
                technologies=["Python", "FastAPI", "Redis"],
            )
        ],
        education=[
            EducationItem(degree="B.S. in Computer Science", institution="MIT", graduation_year=2019)
        ],
    )


@pytest.fixture
def sample_weak_candidate():
    return CandidateProfile(
        id="cand-weak",
        name="David Lee",
        headline="Junior Marketing Coordinator",
        summary="1 year experience in digital marketing and content copywriting.",
        skills=["Copywriting", "SEO", "Google Analytics", "Social Media"],
        experience_years=1.0,
        work_history=[
            WorkExperienceItem(
                title="Marketing Associate",
                company="Growth Agency",
                duration_years=1.0,
                description="Managed email campaigns and social channels.",
            )
        ],
        education=[
            EducationItem(degree="B.A. in Communications", institution="State University", graduation_year=2024)
        ],
    )


def test_models_serialization(sample_jd, sample_strong_candidate):
    """Verifies that models serialize and produce dense text representation."""
    jd_dense = sample_jd.to_dense_text()
    assert "Lead Python Backend Engineer" in jd_dense
    assert "Python" in jd_dense

    cand_dense = sample_strong_candidate.to_dense_text()
    assert "Sarah Connor" in cand_dense
    assert "FastAPI" in cand_dense

    # Test LLMEvaluationOutput validation
    llm_out = LLMEvaluationOutput(
        total_score=85,
        skills_score=90,
        experience_score=80,
        justification="Strong technical match with relevant backend experience.",
    )
    assert llm_out.total_score == 85
    assert llm_out.skills_score == 90


def test_tier1_vector_search(sample_jd, sample_strong_candidate, sample_weak_candidate):
    """Tests Tier 1 Vector Search cosine similarity scoring."""
    engine = VectorSearchEngine()

    strong_score = engine.score_single_candidate(sample_strong_candidate, sample_jd)
    weak_score = engine.score_single_candidate(sample_weak_candidate, sample_jd)

    assert 0.0 <= strong_score <= 100.0
    assert 0.0 <= weak_score <= 100.0
    assert strong_score > weak_score, f"Strong candidate ({strong_score}) should beat weak candidate ({weak_score})"

    # Test indexing & query in ChromaDB
    engine.index_candidates([sample_strong_candidate, sample_weak_candidate])
    ranked = engine.query_similarity(sample_jd, top_k=2)
    assert len(ranked) == 2
    assert ranked[0][0] == sample_strong_candidate.id


def test_tier2_cross_encoder(sample_jd, sample_strong_candidate, sample_weak_candidate):
    """Tests Tier 2 Cross-Encoder deep semantic re-ranking."""
    reranker = CrossEncoderReranker()

    strong_score = reranker.score_pair(sample_strong_candidate, sample_jd)
    weak_score = reranker.score_pair(sample_weak_candidate, sample_jd)

    assert 0.0 <= strong_score <= 100.0
    assert 0.0 <= weak_score <= 100.0
    assert strong_score > weak_score, f"Strong candidate ({strong_score}) should score higher than weak ({weak_score})"


def test_tier3_llm_evaluator(sample_jd, sample_strong_candidate):
    """Tests Tier 3 LLM structured evaluator."""
    evaluator = LLMEvaluator()
    eval_result = evaluator.evaluate(sample_strong_candidate, sample_jd)

    assert isinstance(eval_result, LLMEvaluationOutput)
    assert 0 <= eval_result.total_score <= 100
    assert 0 <= eval_result.skills_score <= 100
    assert 0 <= eval_result.experience_score <= 100
    assert len(eval_result.justification) > 0


def test_end_to_end_orchestration_weighted_score(sample_jd, sample_strong_candidate):
    """Tests complete matching pipeline and weighted score formula."""
    engine = RecruitmentMatchingEngine()
    result = engine.match(sample_strong_candidate, sample_jd)

    assert isinstance(result, TierScoreResult)
    expected_score = round(
        (result.tier1_vector_score * 0.30)
        + (result.tier2_rerank_score * 0.40)
        + (result.tier3_llm_score * 0.30),
        2,
    )
    assert abs(result.final_weighted_score - expected_score) < 0.01
    assert result.final_weighted_score > 60.0
