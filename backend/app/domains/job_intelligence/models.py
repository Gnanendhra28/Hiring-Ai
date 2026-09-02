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
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from app.db.base import Base
from app.domains.document_intelligence.models import EvidenceVerificationStatusEnum

class RequirementTypeEnum(str, enum.Enum):
    SKILL = "SKILL"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"
    CERTIFICATION = "CERTIFICATION"
    LOCATION = "LOCATION"
    WORK_MODE = "WORK_MODE"
    RESPONSIBILITY = "RESPONSIBILITY"
    TECHNOLOGY = "TECHNOLOGY"
    LANGUAGE = "LANGUAGE"
    OTHER = "OTHER"

class RequirementLevelEnum(str, enum.Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    INFORMATIONAL = "INFORMATIONAL"

class RequirementPriorityEnum(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class WorkModeEnum(str, enum.Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"
    FLEXIBLE = "FLEXIBLE"
    UNSPECIFIED = "UNSPECIFIED"

class JobIntelligenceVersionStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    NORMALIZING = "NORMALIZING"
    EVIDENCE_VALIDATION = "EVIDENCE_VALIDATION"
    EMBEDDING = "EMBEDDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    STALE = "STALE"

class JobIntelligenceVersion(Base):
    __tablename__ = "job_intelligence_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    version_number = Column(Integer, nullable=False, default=1)
    source_job_version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=False, index=True)

    status = Column(
        SQLEnum(JobIntelligenceVersionStatusEnum, name="jobintelligenceversionstatusenum"),
        nullable=False,
        default=JobIntelligenceVersionStatusEnum.PENDING,
        index=True,
    )

    ai_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    overall_confidence = Column(Float, nullable=False, default=1.0)
    safe_error_message = Column(Text, nullable=True)

    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    requirement_type = Column(
        SQLEnum(RequirementTypeEnum, name="requirementtypeenum"),
        nullable=False,
        index=True,
    )
    raw_value = Column(String(500), nullable=False)
    canonical_value = Column(String(500), nullable=False, index=True)

    requirement_level = Column(
        SQLEnum(RequirementLevelEnum, name="requirementlevelenum"),
        nullable=False,
        default=RequirementLevelEnum.REQUIRED,
    )
    hard_constraint = Column(Boolean, nullable=False, default=True, index=True)

    operator = Column(String(50), nullable=True)  # GTE, LTE, EQUALS, RANGE
    minimum_value = Column(Float, nullable=True)
    maximum_value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)  # MONTHS, YEARS, DEGREE_LEVEL

    priority = Column(
        SQLEnum(RequirementPriorityEnum, name="requirementpriorityenum"),
        nullable=False,
        default=RequirementPriorityEnum.MEDIUM,
    )

    confidence = Column(Float, nullable=False, default=1.0)
    evidence_text = Column(Text, nullable=True)
    evidence_verification_status = Column(
        SQLEnum(EvidenceVerificationStatusEnum, name="evidenceverificationstatusenum"),
        nullable=False,
        default=EvidenceVerificationStatusEnum.UNVERIFIED,
    )

    is_protected_feature = Column(Boolean, nullable=False, default=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class JobResponsibility(Base):
    __tablename__ = "job_responsibilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    responsibility_text = Column(Text, nullable=False)
    associated_skills = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class JobIntent(Base):
    __tablename__ = "job_intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    raw_intent = Column(Text, nullable=False)
    canonical_intent = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

class JobEmbedding(Base):
    __tablename__ = "job_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    intelligence_version_id = Column(UUID(as_uuid=True), ForeignKey("job_intelligence_versions.id", ondelete="CASCADE"), nullable=False, index=True)

    context_type = Column(String(100), nullable=False, index=True)
    embedding = Column(Vector(1536), nullable=False)
    provider = Column(String(50), nullable=False, default="openai")
    model_name = Column(String(100), nullable=False, default="text-embedding-3-small")
    dimension = Column(Integer, nullable=False, default=1536)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
