import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.db.base import Base

class DocumentProcessingStatusEnum(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    EXTRACTING_TEXT = "EXTRACTING_TEXT"
    OCR_PROCESSING = "OCR_PROCESSING"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    STRUCTURED_EXTRACTION = "STRUCTURED_EXTRACTION"
    EVIDENCE_VALIDATION = "EVIDENCE_VALIDATION"
    EMBEDDING_GENERATION = "EMBEDDING_GENERATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY_REQUIRED = "RETRY_REQUIRED"

class ExtractionMethodEnum(str, enum.Enum):
    NATIVE_PDF = "NATIVE_PDF"
    OCR = "OCR"
    LLM_FAST = "LLM_FAST"
    LLM_STRONG = "LLM_STRONG"

class EvidenceVerificationStatusEnum(str, enum.Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"

class SkillDurationStatusEnum(str, enum.Enum):
    DETERMINISTIC_CALCULATED = "DETERMINISTIC_CALCULATED"
    UNKNOWN = "UNKNOWN"

class CandidateDocument(Base):
    __tablename__ = "candidate_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False, default="application/pdf")

    processing_status = Column(
        SQLEnum(DocumentProcessingStatusEnum, name="documentprocessingstatusenum"),
        nullable=False,
        default=DocumentProcessingStatusEnum.UPLOADED,
        index=True,
    )
    text_quality_score = Column(Float, nullable=True)
    ocr_used = Column(Boolean, nullable=False, default=False)
    ocr_provider = Column(String(50), nullable=True)

    extracted_text = Column(Text, nullable=True)
    safe_error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    raw_skill_name = Column(String(255), nullable=False)
    canonical_skill_name = Column(String(255), nullable=False, index=True)
    years_experience = Column(Float, nullable=True)
    skill_duration_status = Column(
        SQLEnum(SkillDurationStatusEnum, name="skilldurationstatusenum"),
        nullable=False,
        default=SkillDurationStatusEnum.UNKNOWN,
    )
    confidence = Column(Float, nullable=False, default=1.0)
    evidence_text = Column(Text, nullable=True)
    evidence_verification_status = Column(
        SQLEnum(EvidenceVerificationStatusEnum, name="evidenceverificationstatusenum"),
        nullable=False,
        default=EvidenceVerificationStatusEnum.UNVERIFIED,
    )
    page_number = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    raw_start_date = Column(String(50), nullable=True)
    raw_end_date = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    duration_months = Column(Integer, nullable=False, default=0)
    is_current = Column(Boolean, nullable=False, default=False)
    confidence = Column(Float, nullable=False, default=1.0)
    evidence_text = Column(Text, nullable=True)
    evidence_verification_status = Column(
        SQLEnum(EvidenceVerificationStatusEnum, name="evidenceverificationstatusenum"),
        nullable=False,
        default=EvidenceVerificationStatusEnum.UNVERIFIED,
    )
    page_number = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CandidateEducation(Base):
    __tablename__ = "candidate_educations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    evidence_text = Column(Text, nullable=True)
    evidence_verification_status = Column(
        SQLEnum(EvidenceVerificationStatusEnum, name="evidenceverificationstatusenum"),
        nullable=False,
        default=EvidenceVerificationStatusEnum.UNVERIFIED,
    )
    page_number = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CandidateExtractedFact(Base):
    __tablename__ = "candidate_extracted_facts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    fact_type = Column(String(100), nullable=False, index=True)
    raw_value = Column(String(500), nullable=False)
    canonical_value = Column(String(500), nullable=False)
    evidence_text = Column(Text, nullable=True)
    evidence_verification_status = Column(
        SQLEnum(EvidenceVerificationStatusEnum, name="evidenceverificationstatusenum"),
        nullable=False,
        default=EvidenceVerificationStatusEnum.UNVERIFIED,
    )
    page_number = Column(Integer, nullable=True)
    extraction_method = Column(String(50), nullable=False, default="LLM")
    confidence = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class CandidateEmbedding(Base):
    __tablename__ = "candidate_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    context_type = Column(String(100), nullable=False, index=True)
    embedding = Column(Vector(1536), nullable=False)
    provider = Column(String(50), nullable=False, default="openai")
    model_name = Column(String(100), nullable=False, default="text-embedding-3-small")
    dimension = Column(Integer, nullable=False, default=1536)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class AIProcessingAudit(Base):
    __tablename__ = "ai_processing_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("candidate_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    processing_stage = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    confidence = Column(Float, nullable=False, default=1.0)
    escalation_triggered = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
