"""
Candidate Ingestion Pipeline - Data Models
Defines Pydantic V2 schemas for ProfileInput, WorkExperience, Education, and UnifiedCandidateProfile.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class WorkExperience(BaseModel):
    company: str = Field(..., description="Company or organization name")
    title: str = Field(..., description="Job role/title")
    location: Optional[str] = Field(default="", description="City, state/country or Remote")
    start_date: str = Field(..., description="Start date in MM/YYYY format")
    end_date: Optional[str] = Field(default="Present", description="End date in MM/YYYY format or 'Present'")
    is_current: bool = Field(default=False, description="Whether this is the current active role")
    bullet_points: List[str] = Field(default_factory=list, description="Action-oriented summary bullet points")


class Education(BaseModel):
    institution: str = Field(..., description="College or university name")
    degree: str = Field(..., description="Degree type (e.g. B.S., M.S., Ph.D.)")
    field_of_study: Optional[str] = Field(default="", description="Major or area of concentration")
    start_date: Optional[str] = Field(default=None, description="Start date in MM/YYYY format")
    end_date: Optional[str] = Field(default=None, description="Graduation/completion date in MM/YYYY format")
    grade_or_gpa: Optional[str] = Field(default=None, description="GPA or honors distinction")


class Project(BaseModel):
    name: str = Field(..., description="Project title")
    description: str = Field(..., description="Summary of project impact and implementation")
    technologies: List[str] = Field(default_factory=list, description="Tech stack / frameworks used")
    link: Optional[str] = Field(default=None, description="GitHub or live URL")


class Certification(BaseModel):
    name: str = Field(..., description="Certification or credential name")
    issuer: str = Field(..., description="Issuing organization")
    issue_date: Optional[str] = Field(default=None, description="Issue date in MM/YYYY format")


class ProfileInput(BaseModel):
    """Raw structured candidate data from manual onboarding or account registration."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    work_history: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)


class UnifiedCandidateProfile(BaseModel):
    """Reconciled, single source of truth profile merging manual input + resume extraction."""
    full_name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(default="", description="Candidate email address")
    phone: Optional[str] = Field(default="", description="Contact phone number")
    location: Optional[str] = Field(default="", description="Location or primary residence")
    headline: str = Field(..., description="Target role headline")
    professional_summary: str = Field(
        ...,
        description="Cohesive, professional summary synthesising combined qualifications (2-3 sentences max)",
    )
    total_years_experience: float = Field(..., ge=0.0, description="Computed total years of professional experience")
    skills: List[str] = Field(..., description="Canonicalized and deduplicated technical & domain skills")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="Chronological work experiences")
    education: List[Education] = Field(default_factory=list, description="Educational degrees and institutions")
    projects: List[Project] = Field(default_factory=list, description="Key technical projects")
    certifications: List[Certification] = Field(default_factory=list, description="Professional certifications")


class IngestionResponse(BaseModel):
    """API response envelope for /candidates/{candidate_id}/ingest."""
    candidate_id: str
    status: str
    resume_url: str
    raw_text_length: int
    unified_profile: UnifiedCandidateProfile
