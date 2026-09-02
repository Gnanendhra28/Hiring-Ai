import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.domains.ranking.models import RankingVersionStatusEnum
from app.domains.scoring.models import EligibilityStatusEnum

class GenerateRankingRequest(BaseModel):
    top_k: int = Field(default=10, ge=1, le=500, description="Number of top eligible candidates to flag as Top-K")

class CandidateRankingVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    job_intelligence_version_id: uuid.UUID
    scoring_configuration_id: uuid.UUID
    ranking_version: int
    top_k: int
    status: RankingVersionStatusEnum
    candidate_count: int
    eligible_candidate_count: int
    ineligible_candidate_count: int
    unknown_candidate_count: int
    created_at: datetime
    completed_at: datetime

class CandidateJobRankingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    ranking_version_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID | None = None
    candidate_job_score_id: uuid.UUID
    candidate_document_id: uuid.UUID
    job_intelligence_version_id: uuid.UUID
    rank_position: int
    is_top_k: bool
    eligibility_status: EligibilityStatusEnum
    score: float
    score_confidence: float
    created_at: datetime

class RankingListPaginatedResponse(BaseModel):
    ranking_version: CandidateRankingVersionResponse | None = None
    items: list[CandidateJobRankingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class TopKRankingResponse(BaseModel):
    ranking_version: CandidateRankingVersionResponse
    top_k_candidates: list[CandidateJobRankingResponse]
