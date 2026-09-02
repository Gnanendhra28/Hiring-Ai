import pytest
from app.domains.candidates.models import CandidateProfile
from app.domains.candidates.candidate_intelligence import CandidateIntelligenceExtractor
from app.domains.matching.real_matching_engine import RealJobCandidateMatcher

@pytest.mark.asyncio
async def test_real_matching_engine_8_dimensions():
    job_intel = {
        "role_title": "Generative AI Engineer",
        "required_skills": ["Python", "FastAPI", "Generative AI", "RAG"],
        "preferred_skills": ["PyTorch", "Vector Databases", "Docker"],
        "good_to_have": ["Kubernetes", "AWS"],
        "responsibilities": ["Build and deploy generative AI applications using modern LLM architectures"],
        "experience": {"value": "2+ Years", "evidence": "2+ Years required"},
        "education": []
    }

    profile = CandidateProfile(
        user_id="80e19438-953c-45be-8e46-9b4e00a99edb",
        headline="Generative AI Engineer",
        skills=["Python", "FastAPI", "Generative AI", "RAG", "PyTorch", "Docker"],
        experience=[
            {
                "role": "AI Engineer",
                "company": "Tech Corp",
                "description": "Build and deploy generative AI applications using RAG architectures and FastAPI."
            }
        ],
        education=[{"degree": "B.Tech in Computer Science"}]
    )

    cand_intel = CandidateIntelligenceExtractor.extract(
        profile=profile,
        user_full_name="Matta Gnanendhra"
    )

    match_res = RealJobCandidateMatcher.match(
        job_id="test_job_1",
        job_intelligence=job_intel,
        candidate_intelligence=cand_intel
    )

    assert match_res.job_id == "test_job_1"
    assert match_res.candidate_id == "80e19438-953c-45be-8e46-9b4e00a99edb"
    assert match_res.overall_score >= 80.0
    assert match_res.required_skill_coverage == 1.0
    assert match_res.eligibility_status == "PASS"

    # Verify 8-dimension explanation breakdown
    exp = match_res.explanation
    assert exp.required_skill_score == 100.0
    assert exp.responsibility_score == 100.0
    assert exp.experience_score >= 80.0
    assert exp.role_alignment_score == 100.0
    assert exp.preferred_skill_score >= 60.0

    # Verify ground-truth matched requirements evidence
    assert len(match_res.matched_requirements) > 0
    for req in match_res.matched_requirements:
        assert req.evidence is not None and req.evidence != ""
