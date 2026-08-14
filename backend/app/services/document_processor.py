import uuid
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.document_intelligence.models import (
    AIProcessingAudit,
    CandidateDocument,
    CandidateEducation,
    CandidateEmbedding,
    CandidateExperience,
    CandidateExtractedFact,
    CandidateSkill,
    DocumentProcessingStatusEnum,
    EvidenceVerificationStatusEnum,
)
from app.infrastructure.confidence.calculator import ConfidenceCalculator
from app.infrastructure.experience.calculator import ExperienceCalculator
from app.infrastructure.experience.skill_experience import SkillExperienceCalculator
from app.infrastructure.factories import AIGatewayFactory, EmbeddingProviderFactory, OCRProviderFactory
from app.infrastructure.pdf.evidence_verifier import EvidenceVerifier
from app.infrastructure.pdf.extractor import PDFExtractor
from app.infrastructure.skills.normalizer import SkillNormalizer
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus

event_bus = InMemoryEventBus()

class DocumentProcessorService:
    """
    Asynchronous Document Processing Engine for Candidate Resumes.
    Executes PDF extraction, OCR fallback, AI structured extraction, Skill Normalization,
    Evidence Verification, Independent Confidence Calibration, Deterministic Experience Calculation,
    pgvector Embedding Generation, and AI Cost Auditing.
    """

    def __init__(self):
        self.ocr_adapter = OCRProviderFactory.get_provider()
        self.ai_gateway = AIGatewayFactory.get_provider()
        self.embedding_adapter = EmbeddingProviderFactory.get_provider()

    async def process_document(
        self,
        document_id: uuid.UUID,
        organization_id: uuid.UUID,
        candidate_id: uuid.UUID,
        file_bytes: bytes,
    ) -> bool:
        logger.info(f"Starting async document intelligence processing for document_id={document_id}")

        async with async_session_factory() as session:
            await session.begin()
            # Establish tenant & candidate context for RLS session
            await set_tenant_context(session, organization_id=organization_id, user_id=candidate_id)

            # 1. Fetch Candidate Document
            stmt_doc = select(CandidateDocument).where(CandidateDocument.id == document_id)
            doc = (await session.execute(stmt_doc)).scalar_one_or_none()
            if not doc:
                logger.error(f"Candidate document {document_id} not found under tenant RLS context.")
                return False

            try:
                # --- Step 1: Validation ---
                doc.processing_status = DocumentProcessingStatusEnum.VALIDATING
                if doc.file_size_bytes > settings.MAX_RESUME_SIZE_BYTES:
                    doc.processing_status = DocumentProcessingStatusEnum.FAILED
                    doc.safe_error_message = f"File size ({doc.file_size_bytes} bytes) exceeds limit ({settings.MAX_RESUME_SIZE_BYTES} bytes)."
                    await session.commit()
                    return False

                doc.processing_status = DocumentProcessingStatusEnum.VALIDATED

                # --- Step 2: Native PDF Extraction ---
                doc.processing_status = DocumentProcessingStatusEnum.EXTRACTING_TEXT
                pdf_res = PDFExtractor.extract_text(file_bytes)

                extracted_text = pdf_res["full_text"]
                text_quality = pdf_res["text_quality_score"]
                needs_ocr = pdf_res["needs_ocr"]

                # --- Step 3: OCR Fallback if text quality is insufficient ---
                if needs_ocr:
                    doc.processing_status = DocumentProcessingStatusEnum.OCR_PROCESSING
                    ocr_res = await self.ocr_adapter.extract_text_from_pdf(file_bytes)
                    extracted_text = ocr_res["extracted_text"]
                    doc.ocr_used = True
                    doc.ocr_provider = ocr_res["provider"]

                doc.extracted_text = extracted_text
                doc.text_quality_score = text_quality
                doc.processing_status = DocumentProcessingStatusEnum.TEXT_EXTRACTED

                # --- Step 4: Structured Candidate Extraction & AI Gateway ---
                doc.processing_status = DocumentProcessingStatusEnum.STRUCTURED_EXTRACTION
                ai_envelope = await self.ai_gateway.extract_candidate_intelligence(extracted_text, force_strong_model=False)

                # --- Step 5: Evidence Verification & Independent Confidence Calibration ---
                doc.processing_status = DocumentProcessingStatusEnum.EVIDENCE_VALIDATION
                extraction = ai_envelope.extraction

                # Verify Evidence Quotes against raw extracted text
                total_evidence_count = 0
                verified_evidence_count = 0

                verified_skills = []
                for sk in extraction.skills:
                    v_status, v_mult = EvidenceVerifier.verify_evidence(sk.evidence_text, extracted_text)
                    total_evidence_count += 1
                    if v_status != EvidenceVerificationStatusEnum.UNVERIFIED:
                        verified_evidence_count += 1
                    verified_skills.append((sk, v_status, sk.confidence * v_mult))

                verified_exps = []
                dates_valid = True
                exp_dicts = []
                for exp in extraction.experiences:
                    v_status, v_mult = EvidenceVerifier.verify_evidence(exp.evidence_text, extracted_text)
                    total_evidence_count += 1
                    if v_status != EvidenceVerificationStatusEnum.UNVERIFIED:
                        verified_evidence_count += 1

                    start_dt, _ = ExperienceCalculator.parse_date(exp.start_date_str)
                    end_dt, is_curr = ExperienceCalculator.parse_date(exp.end_date_str)

                    if start_dt and end_dt and end_dt < start_dt:
                        dates_valid = False

                    exp_dicts.append({
                        "company_name": exp.company_name,
                        "job_title": exp.job_title,
                        "raw_start_date": exp.start_date_str,
                        "raw_end_date": exp.end_date_str,
                        "start_date": start_dt,
                        "end_date": end_dt,
                        "is_current": exp.is_current,
                        "evidence_text": exp.evidence_text,
                    })
                    verified_exps.append((exp, v_status, exp.confidence * v_mult, start_dt, end_dt, is_curr))

                verified_ratio = (verified_evidence_count / total_evidence_count) if total_evidence_count > 0 else 0.5

                # Calculate Independent Confidence
                conf_calc = ConfidenceCalculator.calculate_confidence(
                    llm_confidence=extraction.overall_confidence,
                    text_quality_score=text_quality,
                    verified_evidence_ratio=verified_ratio,
                    schema_valid=True,
                    dates_valid=dates_valid,
                )
                final_conf = conf_calc["final_confidence"]

                # Configurable Escalation Evaluation
                if final_conf < settings.AI_ESCALATION_CONFIDENCE_THRESHOLD:
                    logger.info(
                        f"Calibrated confidence ({final_conf:.2f}) is below threshold ({settings.AI_ESCALATION_CONFIDENCE_THRESHOLD}). "
                        "Triggering Strong Model Escalation..."
                    )
                    ai_envelope = await self.ai_gateway.extract_candidate_intelligence(extracted_text, force_strong_model=True)
                    extraction = ai_envelope.extraction

                # --- Step 6: Idempotent Database Persistence ---
                # Delete existing extraction records for document_id before inserting new records
                await session.execute(delete(CandidateSkill).where(CandidateSkill.document_id == doc.id))
                await session.execute(delete(CandidateExperience).where(CandidateExperience.document_id == doc.id))
                await session.execute(delete(CandidateEducation).where(CandidateEducation.document_id == doc.id))
                await session.execute(delete(CandidateExtractedFact).where(CandidateExtractedFact.document_id == doc.id))
                await session.execute(delete(CandidateEmbedding).where(CandidateEmbedding.document_id == doc.id))

                # Persist Skills with Skill-Specific Experience Calculation
                for sk, v_status, adj_conf in verified_skills:
                    canonical_name = SkillNormalizer.normalize(sk.skill_name)
                    skill_years, dur_status = SkillExperienceCalculator.calculate_skill_experience(
                        raw_skill_name=sk.skill_name,
                        canonical_skill_name=canonical_name,
                        evidence_text=sk.evidence_text,
                        experiences=exp_dicts,
                    )

                    skill_rec = CandidateSkill(
                        organization_id=doc.organization_id,
                        candidate_id=doc.candidate_id,
                        document_id=doc.id,
                        raw_skill_name=sk.skill_name,
                        canonical_skill_name=canonical_name,
                        years_experience=skill_years,
                        skill_duration_status=dur_status,
                        confidence=round(adj_conf, 2),
                        evidence_text=sk.evidence_text,
                        evidence_verification_status=v_status,
                        page_number=sk.page_number,
                    )
                    session.add(skill_rec)

                # Persist Experiences
                for exp, v_status, adj_conf, start_dt, end_dt, is_curr in verified_exps:
                    dur_months = ExperienceCalculator.calculate_employment_duration_months(start_dt, end_dt)

                    exp_rec = CandidateExperience(
                        organization_id=doc.organization_id,
                        candidate_id=doc.candidate_id,
                        document_id=doc.id,
                        company_name=exp.company_name,
                        job_title=exp.job_title,
                        raw_start_date=exp.start_date_str,
                        raw_end_date=exp.end_date_str,
                        start_date=start_dt,
                        end_date=end_dt,
                        duration_months=dur_months,
                        is_current=exp.is_current or is_curr,
                        confidence=round(adj_conf, 2),
                        evidence_text=exp.evidence_text,
                        evidence_verification_status=v_status,
                        page_number=exp.page_number,
                    )
                    session.add(exp_rec)

                # Calculate Candidate Net Total Work Experience
                total_exp_calc = ExperienceCalculator.calculate_total_experience(exp_dicts)
                logger.info(f"Calculated candidate net work experience: {total_exp_calc['total_years']} years ({total_exp_calc['total_months']} months)")

                # Persist Educations
                for edu in extraction.educations:
                    v_status, v_mult = EvidenceVerifier.verify_evidence(edu.evidence_text, extracted_text)
                    start_dt, _ = ExperienceCalculator.parse_date(edu.start_date_str)
                    end_dt, _ = ExperienceCalculator.parse_date(edu.end_date_str)

                    edu_rec = CandidateEducation(
                        organization_id=doc.organization_id,
                        candidate_id=doc.candidate_id,
                        document_id=doc.id,
                        institution=edu.institution,
                        degree=edu.degree,
                        field_of_study=edu.field_of_study,
                        start_date=start_dt,
                        end_date=end_dt,
                        confidence=round(edu.confidence * v_mult, 2),
                        evidence_text=edu.evidence_text,
                        evidence_verification_status=v_status,
                        page_number=edu.page_number,
                    )
                    session.add(edu_rec)

                # Persist Extracted Facts
                for fact in extraction.facts:
                    v_status, v_mult = EvidenceVerifier.verify_evidence(fact.evidence_text, extracted_text)
                    fact_rec = CandidateExtractedFact(
                        organization_id=doc.organization_id,
                        candidate_id=doc.candidate_id,
                        document_id=doc.id,
                        fact_type=fact.fact_type,
                        raw_value=fact.raw_value,
                        canonical_value=fact.raw_value.title(),
                        evidence_text=fact.evidence_text,
                        evidence_verification_status=v_status,
                        page_number=fact.page_number,
                        extraction_method="LLM",
                        confidence=round(fact.confidence * v_mult, 2),
                    )
                    session.add(fact_rec)

                # --- Step 7: Vector Embedding Generation (pgvector) ---
                doc.processing_status = DocumentProcessingStatusEnum.EMBEDDING_GENERATION

                semantic_units = [
                    ("CANDIDATE_SUMMARY", extracted_text[:1000]),
                    ("SKILL_CONTEXT", ", ".join([s.skill_name for s in extraction.skills])),
                    ("EXPERIENCE_CONTEXT", "; ".join([f"{e.job_title} at {e.company_name}" for e in extraction.experiences])),
                ]

                for context_type, text_content in semantic_units:
                    if text_content.strip():
                        vec = await self.embedding_adapter.generate_embedding(text_content)
                        emb_rec = CandidateEmbedding(
                            organization_id=doc.organization_id,
                            candidate_id=doc.candidate_id,
                            document_id=doc.id,
                            context_type=context_type,
                            embedding=vec,
                            provider=settings.EMBEDDING_PROVIDER,
                            model_name=settings.EMBEDDING_MODEL,
                            dimension=settings.EMBEDDING_DIMENSION,
                            metadata_json={"text_length": len(text_content)},
                        )
                        session.add(emb_rec)

                # --- Step 8: AI Processing Audit ---
                audit_rec = AIProcessingAudit(
                    organization_id=doc.organization_id,
                    candidate_id=doc.candidate_id,
                    document_id=doc.id,
                    processing_stage="COMPLETE_PIPELINE",
                    provider=ai_envelope.provider,
                    model_name=ai_envelope.model_used,
                    input_tokens=ai_envelope.input_tokens,
                    output_tokens=ai_envelope.output_tokens,
                    estimated_cost=ai_envelope.estimated_cost,
                    confidence=final_conf,
                    escalation_triggered=ai_envelope.escalation_triggered,
                )
                session.add(audit_rec)

                audit_log = AuditLog(
                    organization_id=doc.organization_id,
                    user_id=doc.candidate_id,
                    action="document.processed",
                    resource_type="candidate_document",
                    resource_id=str(doc.id),
                )
                session.add(audit_log)

                # --- Step 9: Mark Completed ---
                doc.processing_status = DocumentProcessingStatusEnum.COMPLETED
                await session.commit()

                # Publish Completion Event
                event_envelope = EventEnvelope(
                    event_type="document.processing.completed",
                    aggregate_id=doc.id,
                    organization_id=doc.organization_id,
                    correlation_id=str(uuid.uuid4()),
                    payload={
                        "document_id": str(doc.id),
                        "candidate_id": str(doc.candidate_id),
                        "application_id": str(doc.application_id),
                        "status": "COMPLETED",
                    },
                )
                await event_bus.publish(event_envelope)

                logger.info(f"Successfully finished document intelligence processing for document_id={document_id}")
                return True

            except Exception as e:
                logger.error(f"Error processing candidate document {document_id}: {str(e)}")
                doc.processing_status = DocumentProcessingStatusEnum.FAILED
                doc.safe_error_message = f"Document processing failed: {str(e)}"
                await session.commit()
                return False
