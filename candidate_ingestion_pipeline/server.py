"""
Candidate Ingestion Pipeline - FastAPI Server
Exposes REST endpoints for multipart PDF resume ingestion, text extraction,
LLM reconciliation, and unified profile generation.
"""

import json
import os
import shutil
import uuid
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .extractor import extract_pdf_metadata, extract_text_from_pdf_bytes
from .models import IngestionResponse, ProfileInput, UnifiedCandidateProfile
from .reconciler import CandidateProfileReconciler

app = FastAPI(
    title="Candidate Resume & Profile Ingestion Service",
    version="1.0.0",
    description="Extracts PDF resume text, reconciles it with structured profile data, and generates UnifiedCandidateProfile.",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage Directory for uploaded PDF resumes
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads/resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount local storage static files for recruiter resume viewing
app.mount("/static/resumes", StaticFiles(directory=UPLOAD_DIR), name="resumes")

reconciler_instance = CandidateProfileReconciler()


@app.get("/health")
def health_check():
    """Service health check endpoint."""
    return {"status": "HEALTHY", "service": "candidate-ingestion-pipeline"}


@app.post(
    "/candidates/{candidate_id}/ingest",
    response_model=IngestionResponse,
    status_code=status.HTTP_200_OK,
)
async def ingest_candidate_resume(
    candidate_id: str,
    profile_json: str = Form(default="{}"),
    resume_file: UploadFile = File(...),
):
    """
    Ingests a candidate's resume PDF and profile JSON, parses text, reconciles conflicts,
    and returns a UnifiedCandidateProfile ready for downstream matching.
    """
    # 1. Validate PDF file type
    if not resume_file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported.",
        )

    # 2. Read PDF bytes
    try:
        pdf_bytes = await resume_file.read()
        if not pdf_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF file is empty.",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    # 3. Store raw PDF to storage
    sanitized_filename = f"{candidate_id}_{uuid.uuid4().hex[:8]}_{resume_file.filename}"
    file_path = os.path.join(UPLOAD_DIR, sanitized_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist resume to storage: {str(e)}",
        )

    resume_url = f"/static/resumes/{sanitized_filename}"

    # 4. Extract Text & Metadata using PyMuPDF
    extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
    metadata = extract_pdf_metadata(pdf_bytes)

    # 5. Parse structured ProfileInput JSON
    try:
        raw_profile_dict = json.loads(profile_json) if profile_json else {}
        profile_input = ProfileInput.model_validate(raw_profile_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid profile_json payload: {str(e)}",
        )

    # 6. Reconcile with LLM Engine
    try:
        unified_profile = reconciler_instance.reconcile(profile_input, extracted_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM Data Reconciliation failed: {str(e)}",
        )

    return IngestionResponse(
        candidate_id=candidate_id,
        status="SUCCESS",
        resume_url=resume_url,
        raw_text_length=len(extracted_text),
        unified_profile=unified_profile,
    )
