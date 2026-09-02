import uuid
from datetime import datetime
from typing import Any
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
    company_name: str | None = Field(None, min_length=2, max_length=255)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    portal_type: str | None = None

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str | None = None
    new_password: str = Field(..., min_length=6)

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str | None = None
    requested_role: str | None = "CANDIDATE"

class GoogleAuthUrlResponse(BaseModel):
    url: str | None = None
    configured: bool


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    phone_number: str | None = None
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
    memberships: list[OrganizationMembershipResponse]

# --- Recruiter & Candidate Profile Schemas ---
class RecruiterProfileRequest(BaseModel):
    job_title: str | None = Field(None, max_length=255)
    department: str | None = Field(None, max_length=255)
    phone_number: str | None = Field(None, max_length=50)
    company_name: str | None = Field(None, max_length=255)
    website_url: str | None = Field(None, max_length=500)
    registration_id: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=500)

class RecruiterProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_title: str | None
    department: str | None
    phone_number: str | None
    company_name: str | None
    website_url: str | None
    registration_id: str | None
    linkedin_url: str | None
    verification_status: str
    submitted_at: str | None
    created_at: datetime

class CandidateProfileRequest(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    headline: str | None = Field(None, max_length=255)
    summary: str | None = None
    phone: str | None = Field(None, max_length=50)
    photo_url: str | None = None
    degree: str | None = Field(None, max_length=255)
    college: str | None = Field(None, max_length=255)
    skills: list[str] | None = None
    experience: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None
    career_preferences: dict[str, Any] | None = None
    languages: list[dict[str, Any]] | None = None
    internships: list[dict[str, Any]] | None = None
    projects: list[dict[str, Any]] | None = None
    accomplishments: dict[str, Any] | None = None
    employment: list[dict[str, Any]] | None = None
    website_url: str | None = Field(None, max_length=500)
    linkedin_url: str | None = Field(None, max_length=500)
    resume_url: str | None = Field(None, max_length=500)
    resume_filename: str | None = Field(None, max_length=255)
    resume_filesize: int | None = None
    resume_updated_at: str | None = None

class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    phone: str | None = None
    photo_url: str | None = None
    degree: str | None = None
    college: str | None = None
    skills: list[str] | None = None
    experience: list[Any] | None = None
    education: list[Any] | None = None
    career_preferences: dict[str, Any] | None = None
    languages: list[Any] | None = None
    internships: list[Any] | None = None
    projects: list[Any] | None = None
    accomplishments: dict[str, Any] | None = None
    employment: list[Any] | None = None
    website_url: str | None = None
    linkedin_url: str | None = None
    resume_url: str | None = None
    resume_filename: str | None = None
    resume_filesize: int | None = None
    resume_updated_at: str | None = None
    created_at: datetime

# --- Job Workspace Schemas ---
class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    slug: str | None = Field(None, max_length=255)
    description: str = Field(..., min_length=10)
    department: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: EmploymentTypeEnum = EmploymentTypeEnum.FULL_TIME
    status: JobStatusEnum | None = JobStatusEnum.DRAFT
    verification_status: JobVerificationStatusEnum | None = None
    salary: str | None = Field(None, max_length=255)
    company_website: str | None = Field(None, max_length=512)

class JobUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, min_length=10)
    department: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: EmploymentTypeEnum | None = None
    status: JobStatusEnum | None = None
    verification_status: JobVerificationStatusEnum | None = None
    salary: str | None = Field(None, max_length=255)
    company_website: str | None = Field(None, max_length=512)

class JobVerifyRequest(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    rejection_reason: str | None = Field(None, description="Required when action is REJECT")

class BatchDeleteJobsRequest(BaseModel):
    job_ids: list[uuid.UUID]

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    slug: str
    description: str
    department: str | None
    location: str | None
    employment_type: EmploymentTypeEnum
    status: JobStatusEnum
    verification_status: JobVerificationStatusEnum
    rejection_reason: str | None
    verified_at: datetime | None
    created_by_user_id: uuid.UUID | None
    salary: str | None = None
    company_website: str | None = None
    applications_count: int | None = 0
    ai_shortlisted_count: int | None = 0
    interviews_count: int | None = 0
    skills: list[str] | None = None
    created_at: datetime
    updated_at: datetime

class PublicJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    organization_name: str
    department: str | None
    location: str | None
    employment_type: EmploymentTypeEnum
    description: str
    salary: str | None = None
    company_website: str | None = None
    created_at: datetime

class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int

class PublicJobListResponse(BaseModel):
    items: list[PublicJobResponse]
    total: int
    page: int
    page_size: int

# --- Application Schemas ---
class ApplicationSubmitRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: str | None = Field(None, max_length=255)
    resume_file_path: str | None = Field(None, max_length=500)
    answers_json: dict[str, Any] | None = Field(default_factory=dict)

class ApplicationDecisionRequest(BaseModel):
    action: str = Field(..., description="SHORTLIST or REJECT")
    reason: str | None = Field(None, description="Optional decision notes")

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    organization_id: uuid.UUID
    status: ApplicationStatusEnum
    source: str
    submitted_at: datetime
    resume_id: str | None = None
    resume_file_path: str | None = None
    answers_json: dict[str, Any] | None = None
    created_at: datetime

    candidate_name: str | None = None
    candidate_email: str | None = None
    headline: str | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
    skills: list[str] | None = None

class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
    page: int
    page_size: int

# --- Assessment Schemas ---
class AssessmentCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    duration_minutes: int = Field(60, ge=1, le=480)
    passing_score: int = Field(70, ge=0, le=100)

class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    job_id: uuid.UUID
    title: str
    description: str | None
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
    due_at: datetime | None
    completed_at: datetime | None

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
    notes: str | None = None

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
    meeting_url: str | None
    notes: str | None
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
    validation_json: dict[str, Any] | None
    approved_by_user_id: uuid.UUID | None
    approved_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

# --- Dashboard Metrics Schemas ---
class DashboardMetricsResponse(BaseModel):
    organization_id: uuid.UUID
    active_jobs_count: int
    draft_jobs_count: int
    closed_jobs_count: int
    total_applications_count: int
    shortlisted_count: int = 0
    interview_count: int = 0
    selected_count: int = 0
    rejected_count: int = 0
    recent_jobs: list[JobResponse]
