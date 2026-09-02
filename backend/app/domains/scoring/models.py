import enum
import uuid
from datetime import datetime, UTC

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class EligibilityStatusEnum(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"

class FactorTypeEnum(str, enum.Enum):
    REQUIRED_SKILLS = "REQUIRED_SKILLS"
    SEMANTIC_MATCH = "SEMANTIC_MATCH"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    PREFERRED_SKILLS = "PREFERRED_SKILLS"
    OTHER_REQUIREMENTS = "OTHER_REQUIREMENTS"

class ConfidenceTierEnum(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ScoringProcessingStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ScoringConfiguration(Base):
    """
    Versioned scoring configuration per organization/job.
    Defines configurable factor weights.
    Weights must satisfy: 0 <= weight <= 1 and sum(weights) == 1.0.
    """
    __tablename__ = "scoring_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)

    required_skills_weight = Column(Float, nullable=False, default=0.30)
    semantic_match_weight = Column(Float, nullable=False, default=0.20)
    experience_weight = Column(Float, nullable=False, default=0.20)
    education_weight = Column(Float, nullable=False, default=0.10)
    preferred_skills_weight = Column(Float, nullable=False, default=0.10)
    other_requirements_weight = Column(Float, nullable=False, default=0.10)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class CandidateJobScore(Base):
    """
    Master candidate score record calculated deterministically from Phase 9A feature matches.
    CRITICAL AI GOVERNANCE RULE:
    Contains ZERO LLM-generated overall scores, candidate rankings, Top-K calculations, or automatic status mutations.
    """
    __tablename__ = "candidate_job_scores"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "candidate_id", "job_intelligence_version_id", "candidate_document_id", "scoring_configuration_version",
            name="uq_candidate_job_score_version",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    job_intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)

    scoring_configuration_id = Column(UUID(as_uuid=True), ForeignKey("scoring_configurations.id", ondelete="CASCADE"), nullable=False)
    scoring_configuration_version = Column(Integer, nullable=False, default=1)

    eligibility_status = Column(SQLEnum(EligibilityStatusEnum, name="eligibilitystatusenum"), nullable=False, default=EligibilityStatusEnum.PENDING)
    overall_score = Column(Float, nullable=False, default=0.0)
    score_confidence = Column(Float, nullable=False, default=1.0)
    confidence_tier = Column(SQLEnum(ConfidenceTierEnum, name="confidencetierenum"), nullable=False, default=ConfidenceTierEnum.HIGH)

    status = Column(SQLEnum(ScoringProcessingStatusEnum, name="scoringprocessingstatusenum"), nullable=False, default=ScoringProcessingStatusEnum.COMPLETED)
    safe_error_message = Column(Text, nullable=True)

    calculated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class CandidateFactorScore(Base):
    """
    Granular factor scores breakdown contributing to CandidateJobScore.
    """
    __tablename__ = "candidate_factor_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_job_score_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_scores.id", ondelete="CASCADE"), nullable=False, index=True)

    factor_type = Column(SQLEnum(FactorTypeEnum, name="factortypeenum"), nullable=False, index=True)
    raw_score = Column(Float, nullable=False, default=0.0)          # 0 - 100
    normalized_score = Column(Float, nullable=False, default=0.0)   # 0.0 - 1.0
    configured_weight = Column(Float, nullable=False, default=0.0)  # Configured weight
    normalized_weight = Column(Float, nullable=False, default=0.0)  # Applicable weight normalized
    weighted_contribution = Column(Float, nullable=False, default=0.0) # normalized_score * normalized_weight * 100

    applicable = Column(Boolean, nullable=False, default=True)
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class CandidateHardRequirementResult(Base):
    """
    Detailed results of hard requirement gate checks for CandidateJobScore.
    """
    __tablename__ = "candidate_hard_requirement_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_job_score_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_scores.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("job_requirements.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(50), nullable=False, default="MATCHED")
    candidate_value = Column(String(500), nullable=True)
    required_value = Column(String(500), nullable=True)
    operator = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    evidence_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class ScoringProcessingAudit(Base):
    """
    Audit trail log for candidate scoring processing.
    """
    __tablename__ = "scoring_processing_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_job_score_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_scores.id", ondelete="CASCADE"), nullable=False, index=True)

    processing_started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    processing_completed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    processing_duration_ms = Column(Float, nullable=False, default=0.0)

    status = Column(String(50), nullable=False, default="COMPLETED")
    error_message_safe = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
