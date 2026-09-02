import pytest
from app.domains.candidates.models import CandidateProfile
from app.domains.candidates.candidate_intelligence import CandidateIntelligenceExtractor

@pytest.mark.asyncio
async def test_candidate_intelligence_extraction_ground_truth():
    profile = CandidateProfile(
        user_id="80e19438-953c-45be-8e46-9b4e00a99edb",
        headline="AI Engineer",
        skills=["Python", "FastAPI", "PyTorch", "PostgreSQL"],
        experience=[
            {
                "role": "Computer Vision Engineer",
                "company": "Tech Corp",
                "description": "Developed deep learning models using PyTorch and OpenCV."
            }
        ],
        education=[
            {
                "degree": "B.Tech in Computer Science",
                "institution": "IIT"
            }
        ]
    )

    dummy_resume_text = (
        "Matta Gnanendhra - Resume\n"
        "Position / Title: AI Engineer\n"
        "Summary: Experienced AI Engineer specializing in Deep Learning & FastAPI.\n"
        "Skills: Python, PyTorch, OpenCV, TensorFlow, Docker, Kubernetes, PostgreSQL\n"
    )

    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), dummy_resume_text)
    pdf_bytes = doc.tobytes()

    res = CandidateIntelligenceExtractor.extract(
        profile=profile,
        user_full_name="Matta Gnanendhra",
        pdf_bytes=pdf_bytes
    )

    assert res.candidate_id == "80e19438-953c-45be-8e46-9b4e00a99edb"
    assert res.name == "Matta Gnanendhra"
    assert "AI Engineer" in res.target_roles

    skill_names = [s.name for s in res.skills]
    assert "Python" in skill_names
    assert "FastAPI" in skill_names
    assert "PyTorch" in skill_names
    assert "PostgreSQL" in skill_names
    assert "Docker" in skill_names

    # Ground-truth evidence verification check
    source_lower = (dummy_resume_text + " AI Engineer Python FastAPI PyTorch PostgreSQL B.Tech IIT").lower()
    for s in res.skills:
        assert s.name.lower() in source_lower or s.evidence.lower() != ""

    assert len(res.experience) > 0
    assert res.experience[0].role == "Computer Vision Engineer"
    assert len(res.education) > 0
    assert "B.Tech" in res.education[0].degree or "Computer Science" in res.education[0].degree
