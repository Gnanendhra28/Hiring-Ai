"""
Candidate Resume & Profile Ingestion Pipeline Package
"""

from .extractor import extract_pdf_metadata, extract_text_from_pdf_bytes
from .models import (
    Education,
    IngestionResponse,
    ProfileInput,
    Project,
    UnifiedCandidateProfile,
    WorkExperience,
)
from .reconciler import CandidateProfileReconciler
from .server import app

__all__ = [
    "Education",
    "IngestionResponse",
    "ProfileInput",
    "Project",
    "UnifiedCandidateProfile",
    "WorkExperience",
    "extract_pdf_metadata",
    "extract_text_from_pdf_bytes",
    "CandidateProfileReconciler",
    "app",
]
