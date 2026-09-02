import uuid
from datetime import datetime
from pydantic import BaseModel

class RequirementMatchResponse(BaseModel):
    id: uuid.UUID
    job_requirement_id: uuid.UUID
    requirement_type: str
    raw_required_value: str
    canonical_required_value: str
    requirement_level: str
    hard_constraint: bool
    match_status: str
    candidate_value: str | None = None
    normalized_candidate_value: str | None = None
    confidence: float
    reason: str | None = None
    evidence_text: str | None = None
    evidence_verification_status: str

    class Config:
        from_attributes = True

class SemanticMatchResponse(BaseModel):
    id: uuid.UUID
    query_context: str
    candidate_context: str
    similarity_score: float
    embedding_model: str

    class Config:
        from_attributes = True

class CandidateJobMatchResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    job_intelligence_version_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_document_id: uuid.UUID
    application_id: uuid.UUID | None = None
    matching_version: int
    status: str
    total_requirements_count: int
    matched_requirements_count: int
    hard_requirements_failed_count: int
    ai_provider: str | None = None
    model_name: str | None = None
    embedding_model: str | None = None
    overall_confidence: float
    safe_error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeatureMatchDetailResponse(BaseModel):
    match: CandidateJobMatchResponse
    requirement_matches: list[RequirementMatchResponse]
    semantic_matches: list[SemanticMatchResponse]

class FactorScoreItem(BaseModel):
    score: float
    weight: float
    weighted_total: float

class ScoreBreakdownSchema(BaseModel):
    required_skill_score: float
    responsibility_score: float
    experience_score: float
    role_alignment_score: float
    preferred_skill_score: float
    project_score: float
    education_score: float
    good_to_have_bonus: float
    weighted_total: float

class ExplainableCandidateAnalysisResponse(BaseModel):
    job_id: str
    candidate_id: str
    application_id: str | None = None
    candidate_name: str | None = None
    overall_score: float
    eligibility_status: str
    score_confidence: float
    confidence_tier: str | None = "HIGH"
    rank_position: int | None = 1
    score_breakdown: ScoreBreakdownSchema
    job_intelligence: dict
    candidate_intelligence: dict
    matched_requirements: list[dict] = []
    missing_requirements: list[dict] = []
    strengths: list[str] = []
    gaps: list[str] = []
    evidence_citations: list[dict] = []

