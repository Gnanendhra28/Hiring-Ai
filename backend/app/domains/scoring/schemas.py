import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.domains.scoring.models import (
    ConfidenceTierEnum,
    EligibilityStatusEnum,
    FactorTypeEnum,
    ScoringProcessingStatusEnum,
)

class ScoringConfigurationCreate(BaseModel):
    required_skills_weight: float = Field(default=0.30, ge=0.0, le=1.0)
    semantic_match_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    experience_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    education_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    preferred_skills_weight: float = Field(default=0.10, ge=0.0, le=1.0)
    other_requirements_weight: float = Field(default=0.10, ge=0.0, le=1.0)

class ScoringConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    version_number: int
    is_active: bool
    required_skills_weight: float
    semantic_match_weight: float
    experience_weight: float
    education_weight: float
    preferred_skills_weight: float
    other_requirements_weight: float
    created_at: datetime

class CandidateFactorScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    factor_type: FactorTypeEnum
    raw_score: float
    normalized_score: float
    configured_weight: float
    normalized_weight: float
    weighted_contribution: float
    applicable: bool
    reason: str | None = None
    confidence: float

class HardRequirementResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_id: uuid.UUID
    status: str
    candidate_value: str | None = None
    required_value: str | None = None
    operator: str | None = None
    reason: str | None = None
    confidence: float
    evidence_text: str | None = None

class CandidateJobScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    job_intelligence_version_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_document_id: uuid.UUID
    application_id: uuid.UUID | None = None
    scoring_configuration_id: uuid.UUID
    scoring_configuration_version: int
    eligibility_status: EligibilityStatusEnum
    overall_score: float
    score_confidence: float
    confidence_tier: ConfidenceTierEnum
    status: ScoringProcessingStatusEnum
    safe_error_message: str | None = None
    calculated_at: datetime
    created_at: datetime

class ScoreBreakdownDetailResponse(BaseModel):
    score: CandidateJobScoreResponse
    factor_scores: list[CandidateFactorScoreResponse]
    hard_requirement_results: list[HardRequirementResultResponse]
