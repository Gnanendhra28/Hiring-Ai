import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.domains.recommendation.models import (
    ReasonCodeEnum,
    RecommendationTypeEnum,
    RecruiterDecisionEnum,
    ReviewStateEnum,
)

class GenerateRecommendationRequest(BaseModel):
    candidate_id: uuid.UUID
    top_k_only: bool = Field(default=True, description="Limit automatic batch recommendation generation to Top-K candidates")

class RecruiterDecisionRequest(BaseModel):
    decision: RecruiterDecisionEnum
    decision_reason: str | None = Field(None, max_length=1000, description="Optional recruiter justification")

class RecommendationReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reason_code: ReasonCodeEnum
    reason_type: str
    description: str
    evidence_reference: str | None = None

class RecommendationEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    document_id: uuid.UUID
    page_number: int
    evidence_text: str
    verification_status: str

class CandidateRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID | None = None
    job_intelligence_version_id: uuid.UUID
    candidate_document_id: uuid.UUID
    candidate_job_score_id: uuid.UUID
    ranking_version_id: uuid.UUID
    recommendation_type: RecommendationTypeEnum
    recommendation_confidence: float
    status: str
    summary: str
    strengths: list[str]
    gaps: list[str]
    created_at: datetime

class RecommendationDetailResponse(BaseModel):
    recommendation: CandidateRecommendationResponse
    reasons: list[RecommendationReasonResponse]
    evidence: list[RecommendationEvidenceResponse]

class CandidateDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID
    recommendation_id: uuid.UUID | None = None
    review_state: ReviewStateEnum
    decision: RecruiterDecisionEnum
    decision_reason: str | None = None
    decided_by_user_id: uuid.UUID | None = None
    decided_at: datetime | None = None
    created_at: datetime

class CandidateDecisionAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID
    recommendation_id: uuid.UUID | None = None
    decision: RecruiterDecisionEnum
    previous_state: str
    new_state: str
    decision_reason: str | None = None
    decided_by_user_id: uuid.UUID | None = None
    decided_at: datetime
