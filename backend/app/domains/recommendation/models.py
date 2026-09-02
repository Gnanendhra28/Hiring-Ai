import enum
import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class RecommendationTypeEnum(str, enum.Enum):
    STRONGLY_RECOMMEND_REVIEW = "STRONGLY_RECOMMEND_REVIEW"
    RECOMMEND_REVIEW = "RECOMMEND_REVIEW"
    NEUTRAL_REVIEW = "NEUTRAL_REVIEW"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    NOT_RECOMMENDED_FOR_REVIEW = "NOT_RECOMMENDED_FOR_REVIEW"
    RECOMMENDATION_FAILED = "RECOMMENDATION_FAILED"

class ReviewStateEnum(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    REVIEWED = "REVIEWED"
    DECISION_REQUIRED = "DECISION_REQUIRED"
    DECIDED = "DECIDED"

class RecruiterDecisionEnum(str, enum.Enum):
    ADVANCE = "ADVANCE"
    REJECT = "REJECT"
    HOLD = "HOLD"
    REQUEST_MORE_INFORMATION = "REQUEST_MORE_INFORMATION"
    NO_DECISION = "NO_DECISION"

class ReasonCodeEnum(str, enum.Enum):
    ALL_CRITICAL_REQUIREMENTS_MET = "ALL_CRITICAL_REQUIREMENTS_MET"
    STRONG_REQUIRED_SKILL_ALIGNMENT = "STRONG_REQUIRED_SKILL_ALIGNMENT"
    STRONG_RELEVANT_EXPERIENCE = "STRONG_RELEVANT_EXPERIENCE"
    HIGH_SCORE_CONFIDENCE = "HIGH_SCORE_CONFIDENCE"
    TOP_K_CANDIDATE = "TOP_K_CANDIDATE"
    HARD_REQUIREMENT_FAILED = "HARD_REQUIREMENT_FAILED"
    LOW_SCORE_CONFIDENCE = "LOW_SCORE_CONFIDENCE"
    UNKNOWN_REQUIRED_INFORMATION = "UNKNOWN_REQUIRED_INFORMATION"
    MISSING_REQUIRED_SKILL = "MISSING_REQUIRED_SKILL"
    PREFERRED_SKILL_GAP = "PREFERRED_SKILL_GAP"
    SEMANTIC_ALIGNMENT = "SEMANTIC_ALIGNMENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

class CandidateRecommendation(Base):
    """
    Core AI Recommendation snapshot for a candidate.
    CRITICAL AI GOVERNANCE RULE:
    AI ASSISTS. RECRUITER DECIDES.
    Contains ZERO automated application status mutation fields.
    Does NOT recompute candidate scores or rankings.
    """
    __tablename__ = "candidate_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "candidate_id", "job_intelligence_version_id", "candidate_document_id", "candidate_job_score_id", "ranking_version_id",
            name="uq_candidate_recommendation_version_tuple",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)

    job_intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False)
    candidate_document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False)
    candidate_job_score_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_scores.id", ondelete="CASCADE"), nullable=False)
    ranking_version_id = Column(UUID(as_uuid=True), ForeignKey("candidate_ranking_versions.id", ondelete="CASCADE"), nullable=False)

    recommendation_type = Column(SQLEnum(RecommendationTypeEnum, name="recommendationtypeenum"), nullable=False, default=RecommendationTypeEnum.RECOMMEND_REVIEW)
    recommendation_confidence = Column(Float, nullable=False, default=0.90)
    status = Column(String(50), nullable=False, default="COMPLETED")

    summary = Column(Text, nullable=False, default="")
    strengths = Column(JSON, nullable=False, default=list) # List of strings
    gaps = Column(JSON, nullable=False, default=list)      # List of strings

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class CandidateRecommendationReason(Base):
    """
    Deterministic reason codes backing a candidate recommendation.
    """
    __tablename__ = "candidate_recommendation_reasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("candidate_recommendations.id", ondelete="CASCADE"), nullable=False, index=True)

    reason_code = Column(SQLEnum(ReasonCodeEnum, name="reasoncodeenum"), nullable=False)
    reason_type = Column(String(50), nullable=False, default="POSITIVE") # POSITIVE, NEGATIVE, NEUTRAL
    description = Column(Text, nullable=False)
    evidence_reference = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class CandidateRecommendationEvidence(Base):
    """
    Grounded evidence citations supporting recommendation explanations.
    """
    __tablename__ = "candidate_recommendation_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("candidate_recommendations.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type = Column(String(50), nullable=False, default="CANDIDATE_DOCUMENT")
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False, default=1)
    evidence_text = Column(Text, nullable=False)
    verification_status = Column(String(50), nullable=False, default="VERIFIED")

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class CandidateDecision(Base):
    """
    Active recruiter review state & decision record.
    """
    __tablename__ = "candidate_decisions"
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_candidate_decision_application"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("candidate_recommendations.id", ondelete="SET NULL"), nullable=True)

    review_state = Column(SQLEnum(ReviewStateEnum, name="reviewstateenum"), nullable=False, default=ReviewStateEnum.PENDING_REVIEW)
    decision = Column(SQLEnum(RecruiterDecisionEnum, name="recruiterdecisionenum"), nullable=False, default=RecruiterDecisionEnum.NO_DECISION)
    decision_reason = Column(Text, nullable=True)

    decided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class CandidateDecisionAudit(Base):
    """
    Append-only immutable recruiter decision audit trail.
    """
    __tablename__ = "candidate_decision_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("candidate_recommendations.id", ondelete="SET NULL"), nullable=True)

    decision = Column(SQLEnum(RecruiterDecisionEnum, name="recruiterdecisionenum"), nullable=False)
    previous_state = Column(String(50), nullable=False)
    new_state = Column(String(50), nullable=False)
    decision_reason = Column(Text, nullable=True)

    decided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    correlation_id = Column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class RecommendationProcessingAudit(Base):
    """
    Audit trail for AI recommendation generation processing & cost tracking.
    """
    __tablename__ = "recommendation_processing_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("candidate_recommendations.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = Column(String(50), nullable=False, default="gemini")
    model = Column(String(100), nullable=False, default="gemini-3.5-flash")
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_usd = Column(Float, nullable=False, default=0.0)
    processing_duration_ms = Column(Float, nullable=False, default=0.0)

    status = Column(String(50), nullable=False, default="COMPLETED")
    error_message_safe = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
