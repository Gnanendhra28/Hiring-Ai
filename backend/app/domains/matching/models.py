import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

class MatchStatusEnum(str, enum.Enum):
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    NOT_MATCHED = "NOT_MATCHED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PROTECTED_EXCLUDED = "PROTECTED_EXCLUDED"

class MatchProcessingStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    RETRIEVING = "RETRIEVING"
    HARD_RULE_EVALUATION = "HARD_RULE_EVALUATION"
    SEMANTIC_MATCHING = "SEMANTIC_MATCHING"
    FEATURE_MATCHING = "FEATURE_MATCHING"
    EVIDENCE_MAPPING = "EVIDENCE_MAPPING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    STALE = "STALE"

class CandidateJobMatch(Base):
    """
    Main candidate-job feature matching record.
    Preserves explicit version references to both Job Intelligence Version and Candidate Document/Intelligence Version.
    CRITICAL AI GOVERNANCE RULE: Contains ZERO overall match score or candidate rank.
    """
    __tablename__ = "candidate_job_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    job_intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True)

    matching_version = Column(Integer, nullable=False, default=1)
    status = Column(Enum(MatchProcessingStatusEnum, name="match_processing_status_enum", create_type=False), nullable=False, default=MatchProcessingStatusEnum.PENDING, index=True)
    
    total_requirements_count = Column(Integer, nullable=False, default=0)
    matched_requirements_count = Column(Integer, nullable=False, default=0)
    hard_requirements_failed_count = Column(Integer, nullable=False, default=0)

    ai_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    overall_confidence = Column(Float, nullable=False, default=0.0)
    safe_error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index(
            "uq_candidate_job_match_version",
            "job_id",
            "candidate_id",
            "job_intelligence_version_id",
            "candidate_document_id",
            unique=True,
        ),
    )

class CandidateRequirementMatch(Base):
    """
    Per-requirement feature match between job requirement and candidate evidence.
    """
    __tablename__ = "candidate_requirement_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    job_requirement_id = Column(UUID(as_uuid=True), ForeignKey("job_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    requirement_type = Column(String(50), nullable=False)
    raw_required_value = Column(Text, nullable=False)
    canonical_required_value = Column(String(255), nullable=False)
    requirement_level = Column(String(50), nullable=False)
    hard_constraint = Column(Boolean, nullable=False, default=False)

    match_status = Column(Enum(MatchStatusEnum, name="match_status_enum", create_type=False), nullable=False, default=MatchStatusEnum.UNKNOWN, index=True)
    candidate_value = Column(Text, nullable=True)
    normalized_candidate_value = Column(String(255), nullable=True)
    
    confidence = Column(Float, nullable=False, default=0.0)
    reason = Column(Text, nullable=True)
    evidence_text = Column(Text, nullable=True)
    evidence_verification_status = Column(String(50), nullable=False, default="UNVERIFIED")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class CandidateSemanticMatch(Base):
    """
    Context-aware vector similarity match stored per context pair.
    """
    __tablename__ = "candidate_semantic_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    query_context = Column(String(50), nullable=False)  # e.g., REQUIRED_SKILLS, RESPONSIBILITIES, JOB_INTENT
    candidate_context = Column(String(50), nullable=False)  # e.g., SKILL_CONTEXT, EXPERIENCE_CONTEXT, SUMMARY
    similarity_score = Column(Float, nullable=False)
    
    embedding_model = Column(String(100), nullable=False)
    dimension = Column(Integer, nullable=False, default=1536)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class MatchEvidence(Base):
    """
    Detailed evidence mapping connecting requirement matches to candidate document quotes.
    """
    __tablename__ = "match_evidences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_match_id = Column(UUID(as_uuid=True), ForeignKey("candidate_requirement_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    quote_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    verification_status = Column(String(50), nullable=False, default="UNVERIFIED")
    confidence = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class MatchProcessingAudit(Base):
    """
    Audit log tracking token usage, latency, and AI costs for candidate feature matching.
    """
    __tablename__ = "match_processing_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(UUID(as_uuid=True), ForeignKey("candidate_job_matches.id", ondelete="CASCADE"), nullable=False, index=True)

    processing_stage = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
