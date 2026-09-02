"""
Candidate Ingestion Pipeline - End-to-End Test Suite
Tests PDF generation, text extraction, data reconciliation, and FastAPI endpoint execution.
"""

import json
import pytest
import pymupdf  # PyMuPDF
from httpx import ASGITransport, AsyncClient

from candidate_ingestion_pipeline.extractor import extract_text_from_pdf_bytes
from candidate_ingestion_pipeline.models import ProfileInput, UnifiedCandidateProfile
from candidate_ingestion_pipeline.reconciler import CandidateProfileReconciler
from candidate_ingestion_pipeline.server import app


def create_sample_pdf_bytes() -> bytes:
    """Generates a sample PDF resume in memory using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4

    text = """
ALEX CHEN
Senior AI & Distributed Systems Engineer
San Francisco, CA | alex.chen@stanford.alumni.edu | (415) 555-0199

PROFESSIONAL EXPERIENCE:
VectorAI Technologies — Lead AI Platform Engineer (06/2021 – Present)
- Designed and deployed real-time RAG semantic retrieval microservices in FastAPI.
- Scaled ChromaDB vector collections to 10M+ documents with sub-25ms P99 latency.
- Orchestrated cross-encoder re-ranking pipelines using PyTorch and HuggingFace Transformers.

DataCore Cloud Solutions — Machine Learning Engineer (01/2019 – 05/2021)
- Built containerized model inference workers with Docker, PostgreSQL, and Redis.
- Implemented automated feature store pipelines in Python and Pandas.

TECHNICAL SKILLS:
Languages & Frameworks: Python, FastAPI, PyTorch, Node.js, React, SQL
Databases & Cloud: PostgreSQL, ChromaDB, Redis, Docker, AWS, Kubernetes

EDUCATION:
Stanford University — M.S. in Computer Science (AI Specialization), 2021
UC Berkeley — B.S. in Electrical Engineering & Computer Science, 2018
"""
    # Insert text into PDF page
    rect = pymupdf.Rect(40, 40, 555, 800)
    page.insert_textbox(rect, text, fontsize=10, fontname="helv")

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_pdf_bytes():
    return create_sample_pdf_bytes()


@pytest.fixture
def sample_profile_input():
    return ProfileInput(
        full_name="Alexander Chen",
        email="alex.chen.primary@gmail.com",  # Primary account email (should take precedence over resume email)
        phone="+1-415-555-0199",
        headline="Senior AI Systems Engineer",
        skills=["Python", "FastAPI", "NodeJS", "node", "Docker", "PostgreSQL"],
        years_of_experience=5.5,
    )


def test_pdf_extraction(sample_pdf_bytes):
    """Verifies that PyMuPDF correctly extracts text from PDF bytes."""
    extracted = extract_text_from_pdf_bytes(sample_pdf_bytes)
    assert "ALEX CHEN" in extracted
    assert "VectorAI Technologies" in extracted
    assert "ChromaDB" in extracted
    assert "Stanford University" in extracted


def test_reconciler_logic(sample_pdf_bytes, sample_profile_input):
    """Verifies LLM data reconciliation, conflict resolution, and skill deduplication."""
    extracted_text = extract_text_from_pdf_bytes(sample_pdf_bytes)
    reconciler = CandidateProfileReconciler()

    unified = reconciler.reconcile(sample_profile_input, extracted_text)

    assert isinstance(unified, UnifiedCandidateProfile)
    assert unified.full_name is not None
    # Contact info from profile preferred
    assert unified.email == "alex.chen.primary@gmail.com"
    # Skills deduplication ("node", "NodeJS" -> "Node.js")
    assert "Node.js" in unified.skills
    assert len(unified.skills) > 0
    # Work experience presence
    assert len(unified.work_experience) > 0
    # Professional summary length
    assert len(unified.professional_summary) > 30


@pytest.mark.asyncio
async def test_fastapi_ingest_endpoint(sample_pdf_bytes, sample_profile_input):
    """Tests the end-to-end FastAPI endpoint /candidates/{id}/ingest with multipart upload."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        profile_json_str = json.dumps(sample_profile_input.model_dump())
        files = {
            "resume_file": ("resume_alex_chen.pdf", sample_pdf_bytes, "application/pdf")
        }
        data = {
            "profile_json": profile_json_str
        }

        candidate_id = "cand-alex-001"
        response = await client.post(f"/candidates/{candidate_id}/ingest", data=data, files=files)

        assert response.status_code == 200
        body = response.json()

        assert body["candidate_id"] == candidate_id
        assert body["status"] == "SUCCESS"
        assert body["resume_url"].startswith("/static/resumes/")
        assert body["raw_text_length"] > 100

        profile = body["unified_profile"]
        assert profile["email"] == "alex.chen.primary@gmail.com"
        assert "Node.js" in profile["skills"]
        assert len(profile["work_experience"]) >= 1
        assert len(profile["education"]) >= 1
