import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

class IntegrationBaseEvent(BaseModel):
    event_id: uuid.UUID
    event_type: str
    organization_id: uuid.UUID
    timestamp: datetime

class JobIntelligenceCompletedEvent(IntegrationBaseEvent):
    event_type: str = "job.intelligence.completed"
    job_id: uuid.UUID
    intelligence_version: int
    confidence_score: float

class OfferCreatedEvent(IntegrationBaseEvent):
    event_type: str = "offer.created"
    job_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    placed_by_user_id: uuid.UUID

class OfferAcceptedEvent(IntegrationBaseEvent):
    event_type: str = "offer.accepted"
    job_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID

class CandidateHiredEvent(IntegrationBaseEvent):
    event_type: str = "candidate.hired"
    job_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    time_to_fill_days: Optional[float] = None
    time_to_hire_days: Optional[float] = None
