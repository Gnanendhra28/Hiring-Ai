"""
AI Recruitment Matching Engine - Data Models & Schemas
Defines Pydantic schemas for Candidate, Job Description, LLM Output, and Tier Scores.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkExperienceItem(BaseModel):
    title: str
    company: str
    duration_years: Optional[float] = None
    description: Optional[str] = None


class EducationItem(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[int] = None


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    id: str = Field(..., description="Unique candidate identifier")
    name: str = Field(..., description="Candidate's full name")
    headline: Optional[str] = Field(default="", description="Professional headline/title")
    summary: Optional[str] = Field(default="", description="Summary of qualifications")
    skills: List[str] = Field(default_factory=list, description="Key skills and competencies")
    experience_years: float = Field(default=0.0, description="Total years of professional experience")
    work_history: List[WorkExperienceItem] = Field(default_factory=list, description="Previous roles")
    education: List[EducationItem] = Field(default_factory=list, description="Degrees and credentials")
    projects: List[ProjectItem] = Field(default_factory=list, description="Notable projects")

    def to_dense_text(self) -> str:
        """Converts the candidate profile into a structured dense text representation for semantic embedding."""
        parts = [
            f"Candidate: {self.name}",
            f"Headline: {self.headline}" if self.headline else "",
            f"Summary: {self.summary}" if self.summary else "",
            f"Experience: {self.experience_years} years",
            f"Skills: {', '.join(self.skills)}" if self.skills else "",
        ]

        if self.work_history:
            history_strs = [
                f"{w.title} at {w.company} ({w.duration_years or 'N/A'} yrs): {w.description or ''}"
                for w in self.work_history
            ]
            parts.append("Work History: " + " | ".join(history_strs))

        if self.projects:
            proj_strs = [
                f"{p.name} (Tech: {', '.join(p.technologies)}): {p.description}"
                for p in self.projects
            ]
            parts.append("Projects: " + " | ".join(proj_strs))

        if self.education:
            edu_strs = [f"{e.degree} from {e.institution}" for e in self.education]
            parts.append("Education: " + ", ".join(edu_strs))

        return "\n".join([p for p in parts if p.strip()])


class JobDescription(BaseModel):
    id: str = Field(..., description="Unique job requisition identifier")
    title: str = Field(..., description="Job role title")
    department: Optional[str] = Field(default="", description="Department or business unit")
    required_skills: List[str] = Field(default_factory=list, description="Mandatory required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred/good-to-have skills")
    experience_required_years: float = Field(default=0.0, description="Minimum years of required experience")
    responsibilities: List[str] = Field(default_factory=list, description="Key duties and responsibilities")
    description: str = Field(..., description="Full JD narrative text")

    def to_dense_text(self) -> str:
        """Converts the job description into a structured dense text representation for semantic embedding."""
        parts = [
            f"Role Title: {self.title}",
            f"Department: {self.department}" if self.department else "",
            f"Experience Required: {self.experience_required_years} years",
            f"Required Skills: {', '.join(self.required_skills)}" if self.required_skills else "",
            f"Preferred Skills: {', '.join(self.preferred_skills)}" if self.preferred_skills else "",
        ]

        if self.responsibilities:
            parts.append("Key Responsibilities: " + "; ".join(self.responsibilities))

        if self.description:
            parts.append(f"Description: {self.description}")

        return "\n".join([p for p in parts if p.strip()])


class LLMEvaluationOutput(BaseModel):
    """Structured Pydantic output schema returned by the LLM Evaluator (Tier 3)."""
    total_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall candidate match score evaluated from 0 to 100",
    )
    skills_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Technical and domain skill alignment score from 0 to 100",
    )
    experience_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Relevant experience and seniority match score from 0 to 100",
    )
    justification: str = Field(
        ...,
        description="Concise recruiter evaluation justification (2 sentences max)",
    )


class TierScoreResult(BaseModel):
    """Complete 3-Tier Match Result with weighted score synthesis."""
    candidate_id: str
    candidate_name: str
    job_id: str
    job_title: str

    # Individual Tier Scores (0 - 100)
    tier1_vector_score: float = Field(..., description="Tier 1: ChromaDB Dense Vector Cosine Similarity (0-100)")
    tier2_rerank_score: float = Field(..., description="Tier 2: Cross-Encoder Deep Semantic Relevance (0-100)")
    tier3_llm_score: float = Field(..., description="Tier 3: LLM Structured Total Score (0-100)")

    # Granular Tier 3 Sub-scores
    tier3_skills_score: int
    tier3_experience_score: int
    tier3_justification: str

    # Weighted Final Synthesis Score
    # Formula: (Tier 1 * 0.3) + (Tier 2 * 0.4) + (Tier 3 * 0.3)
    final_weighted_score: float = Field(..., description="Final combined score: (T1*0.3) + (T2*0.4) + (T3*0.3)")
