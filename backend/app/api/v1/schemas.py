import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.domains.applications.models import ApplicationStatusEnum
from app.domains.assessments.models import AssessmentAssignmentStatusEnum
from app.domains.communications.models import CommunicationStatusEnum, WorkflowStageEnum
from app.domains.interviews.models import InterviewStatusEnum, InterviewTypeEnum, MeetingProviderEnum
from app.domains.jobs.models import EmploymentTypeEnum, JobStatusEnum, JobVerificationStatusEnum
from app.domains.organizations.models import MembershipStatusEnum, OrganizationVerificationStatusEnum, RoleEnum

# --- Auth & Identity Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)

class CandidateRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    phone_number: str = Field(..., min_length=7, max_length=50)

class EmployeeRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None
    requested_role: Optional[str] = "CANDIDATE"

class GoogleAuthUrlResponse(BaseModel):
    url: Optional[str] = None
    configured: bool


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    phone_number: Optional[str] = None
    is_platform_admin: bool
    is_active: bool
    is_verified: bool
    created_at: datetime

# --- Organization & Team Schemas ---
class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    verification_status: OrganizationVerificationStatusEnum
    created_at: datetime

class OrganizationMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str
    organization_slug: str
    role: RoleEnum
    status: MembershipStatusEnum

class UserProfileResponse(BaseModel):
    user: UserResponse
    memberships: List[OrganizationMembershipResponse]

# --- Recruiter & Candidate Profile Schemas ---
class RecruiterProfileRequest(BaseModel):
    job_title: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)

class RecruiterProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_title: Optional[str]
    department: Optional[str]
    phone_number: Optional[str]
    created_at: datetime

class CandidateProfileRequest(BaseModel):
    location: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    skills: Optional[List[str]] = Field(default_factory=list)
    experience: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    education: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    website_url: Optional[str] = Field(None, max_length=500)
    linkedin_url: Optional[str] = Field(None, max_length=500)

class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    location: Optional[str]
    headline: Optional[str]
    summary: Optional[str]
    skills: Optional[List[str]]
    experience: Optional[List[Any]]
    education: Optional[List[Any]]
    website_url: Optional[str]
    linkedin_url: Optional[str]
    created_at: datetime

# --- Job Workspace Schemas ---
class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: str = Field(..., min_length=10)
    department: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    employment_type: EmploymentTypeEnum = EmploymentTypeEnum.FULL_TIME

class JobUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    department: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[EmploymentTypeEnum] = None

class JobVerifyRequest(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    rejection_reason: Optional[str] = Field(None, description="Required when action is REJECT")

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    slug: str
    description: str
    department: Optional[str]
    location: Optional[str]
    employment_type: EmploymentTypeEnum
    status: JobStatusEnum
    verification_status: JobVerificationStatusEnum
    rejection_reason: Optional[str]
    verified_at: Optional[datetime]
    created_by_user_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

class PublicJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    organization_name: str
    department: Optional[str]
    location: Optional[str]
    employment_type: EmploymentTypeEnum
    description: str
    created_at: datetime

class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    page_size: int

class PublicJobListResponse(BaseModel):
    items: List[PublicJobResponse]
    total: int
    page: int
    page_size: int

# --- Application Schemas ---
class ApplicationSubmitRequest(BaseModel):
    job_id: uuid.UUID
    resume_file_path: Optional[str] = Field(None, max_length=500)
    answers_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ApplicationDecisionRequest(BaseModel):
    action: str = Field(..., description="SHORTLIST or REJECT")
    reason: Optional[str] = Field(None, description="Optional decision notes")

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    organization_id: uuid.UUID
    status: ApplicationStatusEnum
    source: str
    submitted_at: datetime
    resume_file_path: Optional[str]
    answers_json: Optional[Dict[str, Any]]
    created_at: datetime

class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int

# --- Assessment Schemas ---
class AssessmentCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(60, ge=1, le=480)
    passing_score: int = Field(70, ge=0, le=100)

class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    title: str
    description: Optional[str]
    duration_minutes: int
    passing_score: int
    created_at: datetime

class AssessmentAssignRequest(BaseModel):
    application_id: uuid.UUID
    due_days: int = Field(7, ge=1, le=30)

class AssessmentAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    assessment_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    status: AssessmentAssignmentStatusEnum
    assigned_at: datetime
    due_at: Optional[datetime]
    completed_at: Optional[datetime]

# --- Interview Schemas ---
class InterviewScheduleRequest(BaseModel):
    job_id: uuid.UUID
    application_id: uuid.UUID
    interviewer_user_id: uuid.UUID
    interview_type: InterviewTypeEnum = InterviewTypeEnum.TECHNICAL
    scheduled_start_at: datetime
    duration_minutes: int = Field(45, ge=15, le=240)
    timezone: str = "UTC"
    meeting_provider: MeetingProviderEnum = MeetingProviderEnum.TEST
    notes: Optional[str] = None

class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    application_id: uuid.UUID
    interviewer_user_id: uuid.UUID
    candidate_id: uuid.UUID
    interview_type: InterviewTypeEnum
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    timezone: str
    status: InterviewStatusEnum
    meeting_provider: MeetingProviderEnum
    meeting_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

# --- Communication Schemas ---
class CommunicationDraftRequest(BaseModel):
    job_id: uuid.UUID
    application_id: uuid.UUID
    workflow_stage: WorkflowStageEnum
    recipient_email: EmailStr
    subject: str = Field(..., min_length=2, max_length=500)
    body: str = Field(..., min_length=5)

class CommunicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    application_id: uuid.UUID
    candidate_id: uuid.UUID
    workflow_stage: WorkflowStageEnum
    recipient_email: str
    subject: str
    body: str
    status: CommunicationStatusEnum
    provider: str
    validation_json: Optional[Dict[str, Any]]
    approved_by_user_id: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime

# --- Dashboard Metrics Schemas ---
class DashboardMetricsResponse(BaseModel):
    organization_id: uuid.UUID
    active_jobs_count: int
    draft_jobs_count: int
    closed_jobs_count: int
    total_applications_count: int
    recent_jobs: List[JobResponse]
