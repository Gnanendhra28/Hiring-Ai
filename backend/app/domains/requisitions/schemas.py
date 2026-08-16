import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class FunnelConversionMetrics(BaseModel):
    application_to_eligible_pct: float = 0.0
    eligible_to_top_k_pct: float = 0.0
    top_k_to_reviewed_pct: float = 0.0
    reviewed_to_advanced_pct: float = 0.0
    advanced_to_offer_pct: float = 0.0
    offer_to_accepted_pct: float = 0.0
    accepted_to_hired_pct: float = 0.0

class DecisionAnalytics(BaseModel):
    decision_counts: Dict[str, int] = {"ADVANCE": 0, "REJECT": 0, "HOLD": 0}
    decision_rates_pct: Dict[str, float] = {"advance_rate_pct": 0.0, "reject_rate_pct": 0.0, "hold_rate_pct": 0.0}
    ai_recommendation_distribution: Dict[str, int] = {"RECOMMEND": 0, "REQUIRES_REVIEW": 0, "DO_NOT_RECOMMEND": 0}
    ai_override_sample_size: int = 0
    ai_agreed_count: int = 0
    ai_overridden_count: int = 0
    ai_override_rate_pct: float = 0.0
    ai_override_note: str = "Observational metric only. Sample size n < 30 is insufficient for statistical inference."

class ScoreAnalytics(BaseModel):
    average_score: Optional[float] = None
    median_score: Optional[float] = None
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None
    pass_count: int = 0
    fail_count: int = 0
    confidence_distribution: Dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

class OfferAnalytics(BaseModel):
    offers_extended: int = 0
    offers_accepted: int = 0
    offer_acceptance_rate_pct: float = 0.0
    avg_offer_to_acceptance_days: Optional[float] = None

class RequisitionReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requisition_id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: str
    job_status: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    
    # Intelligence Metadata
    active_intelligence_version: Optional[int] = None
    intelligence_status: Optional[str] = None
    intelligence_confidence: Optional[float] = None

    # Candidate Counts
    total_applications: int = 0
    eligible_applications: int = 0
    ineligible_applications: int = 0
    top_k_candidates: int = 0
    candidates_reviewed: int = 0
    candidates_advanced: int = 0
    candidates_rejected: int = 0
    candidates_held: int = 0
    offers_extended: int = 0
    offers_accepted: int = 0
    candidates_hired: int = 0
    requisition_fill_status: str = "OPEN"

    # Funnel & Analytics
    funnel_conversion: FunnelConversionMetrics = FunnelConversionMetrics()
    decision_analytics: DecisionAnalytics = DecisionAnalytics()
    score_analytics: ScoreAnalytics = ScoreAnalytics()
    offer_analytics: OfferAnalytics = OfferAnalytics()

    # Time Analytics
    time_to_first_candidate_days: Optional[float] = None
    time_to_first_review_days: Optional[float] = None
    time_to_first_decision_days: Optional[float] = None
    time_to_fill_days: Optional[float] = None
    time_to_hire_days: Optional[float] = None

class TenantRequisitionReportResponse(BaseModel):
    organization_id: uuid.UUID
    total_requisitions: int = 0
    total_jobs: int = 0
    active_jobs: int = 0
    requisition_status_counts: Dict[str, int] = {"DRAFT": 0, "PUBLISHED": 0, "PAUSED": 0, "CLOSED": 0}
    total_applications_all_jobs: int = 0
    total_hired_all_jobs: int = 0
    avg_tenant_time_to_fill_days: Optional[float] = None
    avg_tenant_time_to_hire_days: Optional[float] = None

class OrganizationRequisitionPerformanceRow(BaseModel):
    requisition_id: uuid.UUID
    title: str
    status: str
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: str
    applications: int = 0
    eligible: int = 0
    reviewed: int = 0
    advanced: int = 0
    offers: int = 0
    hired: int = 0
    time_to_fill_days: Optional[float] = None
    time_to_hire_days: Optional[float] = None
    intelligence_status: str = "COMPLETED"
    created_at: datetime

class OrganizationDashboardResponse(BaseModel):
    organization_id: uuid.UUID
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    # Requisition Summary
    total_requisitions: int = 0
    open_requisitions: int = 0
    published_requisitions: int = 0
    paused_requisitions: int = 0
    closed_requisitions: int = 0
    filled_requisitions: int = 0

    # Pipeline Totals
    total_applications: int = 0
    eligible_candidates: int = 0
    candidates_advanced: int = 0
    offers_extended: int = 0
    offers_accepted: int = 0
    candidates_hired: int = 0

    # Lifecycle Averages
    avg_time_to_fill_days: Optional[float] = None
    avg_time_to_hire_days: Optional[float] = None
    average_candidate_score: Optional[float] = None

    # Distributions
    pass_fail_distribution: Dict[str, int] = {"PASS": 0, "FAIL": 0}
    confidence_distribution: Dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    # Performance Table
    requisitions: List[OrganizationRequisitionPerformanceRow] = []

class AuditAnalyticsResponse(BaseModel):
    organization_id: uuid.UUID
    total_recruiter_decisions: int = 0
    advance_count: int = 0
    reject_count: int = 0
    hold_count: int = 0
    offer_extended_count: int = 0
    offer_accepted_count: int = 0
    candidate_hired_count: int = 0
    audit_trail_completeness_pct: float = 100.0
    decision_activity_by_requisition: Dict[str, int] = {}

class AIGovernanceAnalyticsResponse(BaseModel):
    organization_id: uuid.UUID
    ai_recommendations_generated: int = 0
    requires_review_count: int = 0
    recommendation_confidence_distribution: Dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    recommendation_generation_failures: int = 0
    recommendation_avg_latency_ms: Optional[float] = None
    recruiter_decisions_count: int = 0
    recommendation_override_count: int = 0
    ai_decision_authority: str = "HUMAN_RECRUITER_ONLY_0_PERCENT_AI_MUTATION"

class AITelemetryResponse(BaseModel):
    organization_id: uuid.UUID
    total_gemini_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retry_count: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    average_latency_ms: Optional[float] = None
