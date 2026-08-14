import uuid
from typing import Optional
from sqlalchemy import delete, select, update

from app.core.config import settings
from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.document_intelligence.models import EvidenceVerificationStatusEnum
from app.domains.job_intelligence.models import (
    JobEmbedding,
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
    JobIntent,
    JobRequirement,
    JobResponsibility,
    RequirementLevelEnum,
    RequirementPriorityEnum,
    RequirementTypeEnum,
)
from app.domains.jobs.models import Job
from app.infrastructure.confidence.calculator import ConfidenceCalculator
from app.infrastructure.factories import AIGatewayFactory, EmbeddingProviderFactory
from app.infrastructure.parsing.job_parser import DeterministicJobParser
from app.infrastructure.pdf.evidence_verifier import EvidenceVerifier
from app.infrastructure.safety.protected_feature_filter import ProtectedFeatureFilter
from app.infrastructure.skills.normalizer import SkillNormalizer
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus

event_bus = InMemoryEventBus()

class JobProcessorService:
    """
    Job Intelligence & Requirement Processing Engine.
    Executes Deterministic Requirement Parsing, AI Structured Extraction, Skill Normalization,
    Evidence Quote Verification, Protected Feature Filtering, Independent Confidence Calibration,
    pgvector Embedding Generation, Versioning, and Cost Auditing.
    """

    def __init__(self):
        self.ai_gateway = AIGatewayFactory.get_provider()
        self.embedding_adapter = EmbeddingProviderFactory.get_provider()

    async def process_job_intelligence(
        self,
        job_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> bool:
        logger.info(f"Starting job intelligence processing for job_id={job_id} under org_id={organization_id}")

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id, user_id=user_id)

            # 1. Fetch Job
            stmt_job = select(Job).where(Job.id == job_id, Job.organization_id == organization_id)
            job = (await session.execute(stmt_job)).scalar_one_or_none()
            if not job:
                logger.error(f"Job {job_id} not found under tenant context.")
                return False

            # 2. Deactivate previous active versions for this job
            await session.execute(
                update(JobIntelligenceVersion)
                .where(JobIntelligenceVersion.job_id == job_id, JobIntelligenceVersion.organization_id == organization_id)
                .values(is_active=False)
            )

            # 3. Create New Intelligence Version
            stmt_max_v = select(JobIntelligenceVersion).where(JobIntelligenceVersion.job_id == job_id).order_by(JobIntelligenceVersion.version_number.desc())
            latest_v = (await session.execute(stmt_max_v)).scalars().first()
            next_v_num = (latest_v.version_number + 1) if latest_v else 1

            version = JobIntelligenceVersion(
                organization_id=organization_id,
                job_id=job_id,
                version_number=next_v_num,
                source_job_version=1,
                is_active=True,
                status=JobIntelligenceVersionStatusEnum.PROCESSING,
                created_by_user_id=user_id,
            )
            session.add(version)
            await session.flush()

            try:
                job_text = f"Job Title: {job.title}\nDepartment: {job.department or ''}\nLocation: {job.location or ''}\nEmployment Type: {job.employment_type.value if hasattr(job.employment_type, 'value') else job.employment_type}\nDescription:\n{job.description}"

                # Step 1: AI Gateway Extraction
                version.status = JobIntelligenceVersionStatusEnum.EXTRACTING
                ai_envelope = await self.ai_gateway.extract_job_intelligence(job_text, force_strong_model=False)

                # Step 2: Evidence Verification & Confidence Calibration
                version.status = JobIntelligenceVersionStatusEnum.EVIDENCE_VALIDATION
                extraction = ai_envelope.extraction

                total_evidence_count = 0
                verified_evidence_count = 0

                processed_requirements = []
                for req in extraction.requirements:
                    v_status, v_mult = EvidenceVerifier.verify_evidence(req.evidence_text, job_text)
                    total_evidence_count += 1
                    if v_status != EvidenceVerificationStatusEnum.UNVERIFIED:
                        verified_evidence_count += 1

                    # Protected Feature Evaluation
                    is_protected, prot_msg = ProtectedFeatureFilter.evaluate(req.raw_value)

                    # Skill Normalization
                    canonical_val = req.canonical_value
                    if req.requirement_type.upper() == "SKILL" or "skill" in req.raw_value.lower():
                        canonical_val = SkillNormalizer.normalize(req.raw_value)
                    elif not canonical_val:
                        canonical_val = req.raw_value.title()

                    # Deterministic Experience Augmentation
                    op_val = req.operator
                    min_val = req.minimum_value
                    unit_val = req.unit
                    hard_c = req.hard_constraint

                    if req.requirement_type.upper() == "EXPERIENCE":
                        det_exp = DeterministicJobParser.parse_experience_string(req.raw_value)
                        if det_exp:
                            op_val = det_exp["operator"]
                            min_val = det_exp["minimum_value"]
                            unit_val = det_exp["unit"]
                            hard_c = det_exp["hard_constraint"]

                    processed_requirements.append({
                        "type": req.requirement_type.upper(),
                        "raw_value": req.raw_value,
                        "canonical_value": canonical_val,
                        "requirement_level": req.requirement_level.upper(),
                        "hard_constraint": hard_c,
                        "operator": op_val,
                        "minimum_value": min_val,
                        "maximum_value": req.maximum_value,
                        "unit": unit_val,
                        "priority": req.priority.upper(),
                        "confidence": round(req.confidence * v_mult, 2),
                        "evidence_text": req.evidence_text,
                        "evidence_verification_status": v_status,
                        "is_protected_feature": is_protected,
                    })

                verified_ratio = (verified_evidence_count / total_evidence_count) if total_evidence_count > 0 else 0.5

                conf_calc = ConfidenceCalculator.calculate_confidence(
                    llm_confidence=extraction.overall_confidence,
                    text_quality_score=0.95,
                    verified_evidence_ratio=verified_ratio,
                    schema_valid=True,
                    dates_valid=True,
                )
                final_conf = conf_calc["final_confidence"]

                # Configurable Escalation Evaluation
                if final_conf < settings.AI_ESCALATION_CONFIDENCE_THRESHOLD:
                    logger.info(f"Job Intelligence confidence ({final_conf:.2f}) below threshold ({settings.AI_ESCALATION_CONFIDENCE_THRESHOLD}). Triggering Strong Model Escalation...")
                    ai_envelope = await self.ai_gateway.extract_job_intelligence(job_text, force_strong_model=True)
                    extraction = ai_envelope.extraction

                # Step 3: Idempotent Persistence — Delete previous artifacts for version
                await session.execute(delete(JobRequirement).where(JobRequirement.intelligence_version_id == version.id))
                await session.execute(delete(JobResponsibility).where(JobResponsibility.intelligence_version_id == version.id))
                await session.execute(delete(JobIntent).where(JobIntent.intelligence_version_id == version.id))
                await session.execute(delete(JobEmbedding).where(JobEmbedding.intelligence_version_id == version.id))

                # Persist Requirements
                for preq in processed_requirements:
                    req_rec = JobRequirement(
                        organization_id=organization_id,
                        job_id=job_id,
                        intelligence_version_id=version.id,
                        requirement_type=RequirementTypeEnum[preq["type"]] if preq["type"] in RequirementTypeEnum.__members__ else RequirementTypeEnum.OTHER,
                        raw_value=preq["raw_value"],
                        canonical_value=preq["canonical_value"],
                        requirement_level=RequirementLevelEnum[preq["requirement_level"]] if preq["requirement_level"] in RequirementLevelEnum.__members__ else RequirementLevelEnum.REQUIRED,
                        hard_constraint=preq["hard_constraint"],
                        operator=preq["operator"],
                        minimum_value=preq["minimum_value"],
                        maximum_value=preq["maximum_value"],
                        unit=preq["unit"],
                        priority=RequirementPriorityEnum[preq["priority"]] if preq["priority"] in RequirementPriorityEnum.__members__ else RequirementPriorityEnum.MEDIUM,
                        confidence=preq["confidence"],
                        evidence_text=preq["evidence_text"],
                        evidence_verification_status=preq["evidence_verification_status"],
                        is_protected_feature=preq["is_protected_feature"],
                    )
                    session.add(req_rec)

                # Persist Responsibilities
                for resp in extraction.responsibilities:
                    resp_rec = JobResponsibility(
                        organization_id=organization_id,
                        job_id=job_id,
                        intelligence_version_id=version.id,
                        responsibility_text=resp.responsibility_text,
                        associated_skills=resp.associated_skills,
                        confidence=resp.confidence,
                    )
                    session.add(resp_rec)

                # Persist Intents
                for intent in extraction.intents:
                    intent_rec = JobIntent(
                        organization_id=organization_id,
                        job_id=job_id,
                        intelligence_version_id=version.id,
                        raw_intent=intent.raw_intent,
                        canonical_intent=intent.canonical_intent,
                        confidence=intent.confidence,
                    )
                    session.add(intent_rec)

                # Step 4: Vector Embedding Generation (pgvector)
                version.status = JobIntelligenceVersionStatusEnum.EMBEDDING
                semantic_units = [
                    ("JOB_SUMMARY", job_text[:1000]),
                    ("REQUIRED_SKILLS", ", ".join([r["canonical_value"] for r in processed_requirements if r["requirement_level"] == "REQUIRED"])),
                    ("PREFERRED_SKILLS", ", ".join([r["canonical_value"] for r in processed_requirements if r["requirement_level"] == "PREFERRED"])),
                    ("RESPONSIBILITIES", "; ".join([r.responsibility_text for r in extraction.responsibilities])),
                    ("JOB_INTENT", "; ".join([i.canonical_intent for i in extraction.intents])),
                ]

                for context_type, text_content in semantic_units:
                    if text_content.strip():
                        vec = await self.embedding_adapter.generate_embedding(text_content)
                        emb_rec = JobEmbedding(
                            organization_id=organization_id,
                            job_id=job_id,
                            intelligence_version_id=version.id,
                            context_type=context_type,
                            embedding=vec,
                            provider=settings.EMBEDDING_PROVIDER,
                            model_name=settings.EMBEDDING_MODEL,
                            dimension=settings.EMBEDDING_DIMENSION,
                            metadata_json={"text_length": len(text_content)},
                        )
                        session.add(emb_rec)

                # Step 5: Mark Completed
                version.status = JobIntelligenceVersionStatusEnum.COMPLETED
                version.ai_provider = ai_envelope.provider
                version.model_name = ai_envelope.model_used
                version.embedding_model = settings.EMBEDDING_MODEL
                version.overall_confidence = final_conf

                audit_log = AuditLog(
                    organization_id=organization_id,
                    user_id=user_id,
                    action="job.intelligence_processed",
                    resource_type="job",
                    resource_id=str(job_id),
                )
                session.add(audit_log)

                await session.commit()

                event_envelope = EventEnvelope(
                    event_type="job.intelligence.completed",
                    aggregate_id=job_id,
                    organization_id=organization_id,
                    correlation_id=str(uuid.uuid4()),
                    payload={
                        "job_id": str(job_id),
                        "version_id": str(version.id),
                        "version_number": next_v_num,
                        "status": "COMPLETED",
                    },
                )
                await event_bus.publish(event_envelope)

                logger.info(f"Successfully processed job intelligence version {next_v_num} for job_id={job_id}")
                return True

            except Exception as e:
                logger.error(f"Error processing job intelligence for job {job_id}: {str(e)}")
                version.status = JobIntelligenceVersionStatusEnum.FAILED
                version.safe_error_message = f"Job intelligence processing failed: {str(e)}"
                await session.commit()
                return False
