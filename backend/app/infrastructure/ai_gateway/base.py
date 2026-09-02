from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import logger


# --- Pydantic Schemas for Strict Output Validation ---
class ExtractedSkillSchema(BaseModel):
    skill_name: str
    years_experience: float | None = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    evidence_text: str | None = ""
    page_number: int | None = 1

class ExtractedExperienceSchema(BaseModel):
    company_name: str
    job_title: str
    start_date_str: str | None = None
    end_date_str: str | None = None
    is_current: bool = False
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    evidence_text: str | None = ""
    page_number: int | None = 1

class ExtractedEducationSchema(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date_str: str | None = None
    end_date_str: str | None = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    evidence_text: str | None = ""
    page_number: int | None = 1

class ExtractedFactSchema(BaseModel):
    fact_type: str
    raw_value: str
    evidence_text: str | None = ""
    page_number: int | None = 1
    confidence: float = Field(1.0, ge=0.0, le=1.0)

class CandidateExtractionSchema(BaseModel):
    skills: list[ExtractedSkillSchema] = Field(default_factory=list)
    experiences: list[ExtractedExperienceSchema] = Field(default_factory=list)
    educations: list[ExtractedEducationSchema] = Field(default_factory=list)
    facts: list[ExtractedFactSchema] = Field(default_factory=list)
    overall_confidence: float = Field(0.9, ge=0.0, le=1.0)

class AIResultEnvelope(BaseModel):
    extraction: CandidateExtractionSchema
    model_used: str
    provider: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    escalation_triggered: bool

# --- Job Intelligence Extraction Schemas ---
class JobExtractedRequirementSchema(BaseModel):
    requirement_type: str = "SKILL"
    raw_value: str
    canonical_value: str | None = None
    requirement_level: str = "REQUIRED"  # REQUIRED, PREFERRED, INFORMATIONAL
    hard_constraint: bool = True
    operator: str | None = None  # GTE, LTE, EQUALS, RANGE
    minimum_value: float | None = None
    maximum_value: float | None = None
    unit: str | None = None
    priority: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    evidence_text: str

class JobExtractedResponsibilitySchema(BaseModel):
    responsibility_text: str
    associated_skills: list[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)

class JobExtractedIntentSchema(BaseModel):
    raw_intent: str
    canonical_intent: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)

class JobExtractionSchema(BaseModel):
    requirements: list[JobExtractedRequirementSchema] = Field(default_factory=list)
    responsibilities: list[JobExtractedResponsibilitySchema] = Field(default_factory=list)
    intents: list[JobExtractedIntentSchema] = Field(default_factory=list)
    overall_confidence: float = Field(0.9, ge=0.0, le=1.0)

class JobAIResultEnvelope(BaseModel):
    extraction: JobExtractionSchema
    model_used: str
    provider: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    escalation_triggered: bool

class AIGatewayProvider(ABC):
    """Abstract Base Class for AI Gateways (OpenAI, Gemini, Anthropic, Mock)."""

    @abstractmethod
    async def extract_candidate_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> AIResultEnvelope:
        pass

    @abstractmethod
    async def extract_job_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> JobAIResultEnvelope:
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> dict[str, Any]:
        """Generate unstructured or narrative chat completion."""
        pass


class TestAIGatewayAdapter(AIGatewayProvider):
    """Controlled AI Gateway Adapter for Local Development & Integration Testing."""

    async def extract_candidate_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> AIResultEnvelope:
        logger.info(f"Executing Test AI Gateway Candidate Extraction (force_strong={force_strong_model})")

        model_name = settings.AI_STRONG_MODEL if force_strong_model else settings.AI_FAST_MODEL
        confidence = 0.95 if force_strong_model else 0.85

        extraction = CandidateExtractionSchema(
            skills=[
                ExtractedSkillSchema(
                    skill_name="Python",
                    years_experience=5.0,
                    confidence=confidence,
                    evidence_text="5+ years experience building Python microservices",
                    page_number=1,
                ),
                ExtractedSkillSchema(
                    skill_name="Retrieval Augmented Generation",
                    years_experience=2.0,
                    confidence=confidence,
                    evidence_text="Built retrieval augmented generation applications using pgvector",
                    page_number=1,
                ),
                ExtractedSkillSchema(
                    skill_name="FastAPI",
                    years_experience=3.0,
                    confidence=confidence,
                    evidence_text="Developed REST APIs using FastAPI and Pydantic",
                    page_number=1,
                ),
            ],
            experiences=[
                ExtractedExperienceSchema(
                    company_name="Acme AI Corp",
                    job_title="Senior Software Engineer",
                    start_date_str="2022-01-01",
                    end_date_str="2025-01-01",
                    is_current=False,
                    confidence=confidence,
                    evidence_text="Senior Software Engineer at Acme AI Corp from 2022 to 2025",
                    page_number=1,
                ),
            ],
            educations=[
                ExtractedEducationSchema(
                    institution="Stanford University",
                    degree="Bachelor of Science",
                    field_of_study="Computer Science",
                    start_date_str="2016-09-01",
                    end_date_str="2020-06-01",
                    confidence=confidence,
                    evidence_text="BS in Computer Science from Stanford University",
                    page_number=1,
                ),
            ],
            facts=[
                ExtractedFactSchema(
                    fact_type="CERTIFICATION",
                    raw_value="AWS Certified Solutions Architect",
                    evidence_text="AWS Certified Solutions Architect - Associate",
                    page_number=1,
                    confidence=confidence,
                ),
                ExtractedFactSchema(
                    fact_type="LOCATION",
                    raw_value="San Francisco, CA",
                    evidence_text="Located in San Francisco, CA",
                    page_number=1,
                    confidence=confidence,
                ),
            ],
            overall_confidence=confidence,
        )

        return AIResultEnvelope(
            extraction=extraction,
            model_used=model_name,
            provider="TEST_AI_GATEWAY",
            input_tokens=450,
            output_tokens=320,
            estimated_cost=0.0015 if force_strong_model else 0.0003,
            escalation_triggered=force_strong_model,
        )

    async def extract_job_intelligence(
        self, text: str, force_strong_model: bool = False
    ) -> JobAIResultEnvelope:
        logger.info(f"Executing Test AI Gateway Job Extraction (force_strong={force_strong_model})")

        model_name = settings.AI_STRONG_MODEL if force_strong_model else settings.AI_FAST_MODEL
        confidence = 0.96 if force_strong_model else 0.88

        extraction = JobExtractionSchema(
            requirements=[
                JobExtractedRequirementSchema(
                    requirement_type="SKILL",
                    raw_value="Python",
                    canonical_value="Python",
                    requirement_level="REQUIRED",
                    hard_constraint=True,
                    priority="HIGH",
                    confidence=confidence,
                    evidence_text="Must have 3+ years of Python development experience.",
                ),
                JobExtractedRequirementSchema(
                    requirement_type="EXPERIENCE",
                    raw_value="3+ years of backend development",
                    canonical_value="3+ years backend development",
                    requirement_level="REQUIRED",
                    hard_constraint=True,
                    operator="GTE",
                    minimum_value=36.0,
                    unit="MONTHS",
                    priority="CRITICAL",
                    confidence=confidence,
                    evidence_text="Must have 3+ years of Python development experience.",
                ),
                JobExtractedRequirementSchema(
                    requirement_type="SKILL",
                    raw_value="Retrieval Augmented Generation",
                    canonical_value="RAG",
                    requirement_level="PREFERRED",
                    hard_constraint=False,
                    priority="MEDIUM",
                    confidence=confidence,
                    evidence_text="Experience building Retrieval Augmented Generation applications is preferred.",
                ),
                JobExtractedRequirementSchema(
                    requirement_type="EDUCATION",
                    raw_value="Bachelor of Science in Computer Science",
                    canonical_value="BS in Computer Science",
                    requirement_level="REQUIRED",
                    hard_constraint=True,
                    priority="MEDIUM",
                    confidence=confidence,
                    evidence_text="Requires a BS in Computer Science or equivalent.",
                ),
                JobExtractedRequirementSchema(
                    requirement_type="WORK_MODE",
                    raw_value="Hybrid - 3 days in office",
                    canonical_value="HYBRID",
                    requirement_level="REQUIRED",
                    hard_constraint=True,
                    priority="HIGH",
                    confidence=confidence,
                    evidence_text="Hybrid role working 3 days in office.",
                ),
            ],
            responsibilities=[
                JobExtractedResponsibilitySchema(
                    responsibility_text="Build and optimize high-throughput RAG search pipelines.",
                    associated_skills=["Python", "RAG", "pgvector"],
                    confidence=confidence,
                )
            ],
            intents=[
                JobExtractedIntentSchema(
                    raw_intent="Build production AI and search services",
                    canonical_intent="AI Application Engineering",
                    confidence=confidence,
                )
            ],
            overall_confidence=confidence,
        )

        return JobAIResultEnvelope(
            extraction=extraction,
            model_used=model_name,
            provider="TEST_AI_GATEWAY",
            input_tokens=520,
            output_tokens=380,
            estimated_cost=0.0018 if force_strong_model else 0.0004,
            escalation_triggered=force_strong_model,
        )

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> dict[str, Any]:
        """Test chat completion returning deterministic narrative for testing environments."""
        return {
            "content": "Candidate demonstrates high alignment with core technical requirements based on evaluation.",
            "model": settings.AI_FAST_MODEL,
            "provider": "TEST_AI_GATEWAY",
            "input_tokens": 150,
            "output_tokens": 80,
            "estimated_cost": 0.0001,
        }

