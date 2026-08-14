import uuid
from datetime import datetime
from typing import List, Optional
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
    candidate_value: Optional[str] = None
    normalized_candidate_value: Optional[str] = None
    confidence: float
    reason: Optional[str] = None
    evidence_text: Optional[str] = None
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
    application_id: Optional[uuid.UUID] = None
    matching_version: int
    status: str
    total_requirements_count: int
    matched_requirements_count: int
    hard_requirements_failed_count: int
    ai_provider: Optional[str] = None
    model_name: Optional[str] = None
    embedding_model: Optional[str] = None
    overall_confidence: float
    safe_error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeatureMatchDetailResponse(BaseModel):
    match: CandidateJobMatchResponse
    requirement_matches: List[RequirementMatchResponse]
    semantic_matches: List[SemanticMatchResponse]
