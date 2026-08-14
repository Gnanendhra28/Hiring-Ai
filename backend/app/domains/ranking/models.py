import enum
import uuid
from datetime import datetime, timezone

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
from app.domains.scoring.models import EligibilityStatusEnum

class RankingVersionStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STALE = "STALE"

class CandidateRankingVersion(Base):
    """
    Versioned ranking snapshot record for a job requisition.
    Maintains historical ranking snapshots for auditability and compliance.
    """
    __tablename__ = "candidate_ranking_versions"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "ranking_version",
            name="uq_candidate_ranking_version_num",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    job_intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    scoring_configuration_id = Column(UUID(as_uuid=True), ForeignKey("scoring_configurations.id", ondelete="CASCADE"), nullable=False)
    
    ranking_version = Column(Integer, nullable=False, default=1)
    top_k = Column(Integer, nullable=False, default=10)
    status = Column(SQLEnum(RankingVersionStatusEnum, name="rankingversionstatusenum"), nullable=False, default=RankingVersionStatusEnum.COMPLETED)
    
    candidate_count = Column(Integer, nullable=False, default=0)
    eligible_candidate_count = Column(Integer, nullable=False, default=0)
    ineligible_candidate_count = Column(Integer, nullable=False, default=0)
    unknown_candidate_count = Column(Integer, nullable=False, default=0)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class CandidateJobRanking(Base):
    """
    Normalized candidate ranking result in a specific ranking snapshot version.
    CRITICAL AI GOVERNANCE RULE:
    Zero LLM involvement in ranking or score calculations.
    Authoritative score originates strictly from Phase 9B CandidateJobScore.
    Contains ZERO automated application status mutation fields.
    """
    __tablename__ = "candidate_job_rankings"
    __table_args__ = (
        UniqueConstraint(
            "ranking_version_id", "candidate_id",
            name="uq_candidate_job_ranking_version_candidate",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    ranking_version_id = Column(UUID(as_uuid=True), ForeignKey("candidate_ranking_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)
    
    candidate_job_score_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_scores.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False)
    job_intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False)

    rank_position = Column(Integer, nullable=False, index=True)
    is_top_k = Column(Boolean, nullable=False, default=False, index=True)
    eligibility_status = Column(SQLEnum(EligibilityStatusEnum, name="eligibilitystatusenum"), nullable=False, index=True)
    
    score = Column(Float, nullable=False, default=0.0)
    score_confidence = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class RankingProcessingAudit(Base):
    """
    Audit trail log for candidate ranking generation.
    """
    __tablename__ = "ranking_processing_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    ranking_version_id = Column(UUID(as_uuid=True), ForeignKey("candidate_ranking_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    processing_started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processing_completed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processing_duration_ms = Column(Float, nullable=False, default=0.0)
    
    status = Column(String(50), nullable=False, default="COMPLETED")
    error_message_safe = Column(Text, nullable=True)
    correlation_id = Column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))


    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
