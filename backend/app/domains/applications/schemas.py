import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.domains.applications.models import OfferStatusEnum, ApplicationStatusEnum

class PlacementActionRequest(BaseModel):
    notes: Optional[str] = None

class CandidatePlacementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID
    offer_status: OfferStatusEnum
    offer_created_at: Optional[datetime] = None
    offer_accepted_at: Optional[datetime] = None
    placed_at: Optional[datetime] = None
    created_by_user_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    time_to_fill_days: Optional[float] = None
    time_to_hire_days: Optional[float] = None
