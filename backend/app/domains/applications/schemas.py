import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.domains.applications.models import OfferStatusEnum

class PlacementActionRequest(BaseModel):
    notes: str | None = None

class CandidatePlacementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID
    offer_status: OfferStatusEnum
    offer_created_at: datetime | None = None
    offer_accepted_at: datetime | None = None
    placed_at: datetime | None = None
    created_by_user_id: uuid.UUID | None = None
    notes: str | None = None
    time_to_fill_days: float | None = None
    time_to_hire_days: float | None = None
