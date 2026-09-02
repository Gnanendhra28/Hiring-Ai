import uuid
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.candidates.models import CandidateProfile
from app.domains.document_intelligence.models import CandidateDocument, CandidateSkill, CandidateExperience

from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
    JobRequirement,
)
from app.domains.matching.models import (
    CandidateJobMatch,
    CandidateRequirementMatch,
    CandidateSemanticMatch,
    MatchProcessingAudit,
    MatchProcessingStatusEnum,
    MatchStatusEnum,
)
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus
from app.infrastructure.matching.hard_rule_engine import HardRequirementEngine
from app.infrastructure.matching.semantic_matcher import SemanticMatcher
from app.infrastructure.matching.skill_matcher import SkillMatcher

event_bus = InMemoryEventBus()

class MatchingService:
    """
    Candidate Retrieval & Feature Matching Engine Service.
    Evaluates Versioned Job Intelligence against Candidate AI Intelligence.
    Produces structured feature-level match results, hard requirement verification,
    skill normalization, evidence mapping, and pgvector semantic context similarities.
    
    CRITICAL AI GOVERNANCE RULE:
    Contains ZERO overall candidate match score, candidate rank, or shortlist/reject logic.
    """

    async def process_candidate_matching(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        application_id: uuid.UUID | None = None,
    ) -> bool:
        logger.info(f"Starting candidate feature matching for job_id={job_id}, candidate_id={candidate_id} under org_id={organization_id}")

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id, user_id=user_id)

            # 1. Fetch Active Job Intelligence Version & STALE Guard
            stmt_job_intel = select(JobIntelligenceVersion).where(
                JobIntelligenceVersion.job_id == job_id,
                JobIntelligenceVersion.organization_id == organization_id,
                JobIntelligenceVersion.is_active.is_(True),
            )
            job_intel_v = (await session.execute(stmt_job_intel)).scalar_one_or_none()

            if not job_intel_v:
                logger.error(f"No active job intelligence version found for job {job_id}.")
                return False

            if job_intel_v.status == JobIntelligenceVersionStatusEnum.STALE:
                logger.error(f"Active job intelligence version {job_intel_v.version_number} for job {job_id} is STALE. Regeneration required before matching.")
                return False

            # 2. Fetch Latest Candidate Document
            stmt_cand_p = select(CandidateProfile).where(CandidateProfile.id == candidate_id)
            cand_p = (await session.execute(stmt_cand_p)).scalar_one_or_none()
            cand_user_id = cand_p.user_id if cand_p else candidate_id

            stmt_doc = select(CandidateDocument).where(
                (CandidateDocument.candidate_id == cand_user_id) | (CandidateDocument.candidate_id == candidate_id),
                CandidateDocument.organization_id == organization_id,
            ).order_by(CandidateDocument.created_at.desc())

            cand_doc = (await session.execute(stmt_doc)).scalars().first()

            if not cand_doc:
                logger.error(f"No candidate document found for candidate {candidate_id} (user_id={cand_user_id}).")
                return False

            # 3. Fetch Job Requirements
            stmt_reqs = select(JobRequirement).where(
                JobRequirement.intelligence_version_id == job_intel_v.id,
                JobRequirement.organization_id == organization_id,
            )
            job_reqs = list((await session.execute(stmt_reqs)).scalars().all())

            # 4. Fetch Candidate Extracted Skills & Experiences & Resume Text
            stmt_cand_skills = select(CandidateSkill).where(
                (CandidateSkill.candidate_id == cand_user_id) | (CandidateSkill.candidate_id == candidate_id)
            )
            cand_skills_raw = list((await session.execute(stmt_cand_skills)).scalars().all())
            cand_skills = [{"skill_name": s.raw_skill_name} for s in cand_skills_raw]

            stmt_cand_exp = select(CandidateExperience).where(
                (CandidateExperience.candidate_id == cand_user_id) | (CandidateExperience.candidate_id == candidate_id)
            )
            cand_exps = list((await session.execute(stmt_cand_exp)).scalars().all())
            total_cand_exp_months = sum([e.duration_months or 0 for e in cand_exps]) or None


            resume_text = cand_doc.extracted_text or ""

            # 5. Idempotent Persistence — Delete prior match records for this version pair
            stmt_prev_match = select(CandidateJobMatch).where(
                CandidateJobMatch.job_id == job_id,
                CandidateJobMatch.candidate_id == candidate_id,
                CandidateJobMatch.job_intelligence_version_id == job_intel_v.id,
                CandidateJobMatch.candidate_document_id == cand_doc.id,
            )
            prev_match = (await session.execute(stmt_prev_match)).scalar_one_or_none()

            if prev_match:
                await session.execute(delete(CandidateRequirementMatch).where(CandidateRequirementMatch.match_id == prev_match.id))
                await session.execute(delete(CandidateSemanticMatch).where(CandidateSemanticMatch.match_id == prev_match.id))
                await session.execute(delete(MatchProcessingAudit).where(MatchProcessingAudit.match_id == prev_match.id))
                await session.delete(prev_match)
                await session.flush()

            # Create Master CandidateJobMatch Record
            match_rec = CandidateJobMatch(
                organization_id=organization_id,
                job_id=job_id,
                job_intelligence_version_id=job_intel_v.id,
                candidate_id=candidate_id,
                candidate_document_id=cand_doc.id,
                application_id=application_id,
                matching_version=1,
                status=MatchProcessingStatusEnum.PROCESSING,
                ai_provider="SYSTEM_HYBRID",
                model_name=settings.EMBEDDING_MODEL,
                embedding_model=settings.EMBEDDING_MODEL,
                overall_confidence=0.90,
            )
            session.add(match_rec)
            await session.flush()

            try:
                matched_cnt = 0
                hard_failed_cnt = 0

                # Stage 1: Requirement Feature Matching
                match_rec.status = MatchProcessingStatusEnum.FEATURE_MATCHING
                for req in job_reqs:
                    if req.is_protected_feature:
                        req_status = MatchStatusEnum.PROTECTED_EXCLUDED
                        conf = 0.0
                        reason = "Requirement flagged as protected feature; excluded from candidate matching."
                        cand_val = None
                        norm_cand_val = None
                        ev_text = None
                        ev_v_status = "EXCLUDED"
                    elif req.requirement_type.name == "SKILL" or req.requirement_type.name == "TECHNOLOGY":
                        req_status, conf, reason, ev_text, ev_v_status = SkillMatcher.match_skill(
                            raw_required_skill=req.raw_value,
                            canonical_required_skill=req.canonical_value,
                            candidate_skills=cand_skills,
                            candidate_resume_text=resume_text,
                            is_protected_feature=req.is_protected_feature,
                        )
                        cand_val = req.canonical_value if req_status == MatchStatusEnum.MATCHED else None
                        norm_cand_val = cand_val
                    elif req.requirement_type.name == "EXPERIENCE":
                        req_status, reason = HardRequirementEngine.evaluate_experience(
                            required_operator=req.operator,
                            required_min_months=req.minimum_value,
                            required_max_months=req.maximum_value,
                            candidate_experience_months=total_cand_exp_months,
                        )
                        conf = 0.90 if req_status != MatchStatusEnum.UNKNOWN else 0.50
                        cand_val = f"{total_cand_exp_months} months" if total_cand_exp_months else None
                        norm_cand_val = cand_val
                        ev_text = None
                        ev_v_status = "VERIFIED" if total_cand_exp_months else "UNVERIFIED"
                    else:
                        req_status = MatchStatusEnum.UNKNOWN
                        conf = 0.50
                        reason = f"Requirement type '{req.requirement_type.name}' evaluated as UNKNOWN (absence of evidence)."
                        cand_val = None
                        norm_cand_val = None
                        ev_text = None
                        ev_v_status = "UNVERIFIED"

                    if req_status == MatchStatusEnum.MATCHED:
                        matched_cnt += 1
                    elif req_status == MatchStatusEnum.NOT_MATCHED and req.hard_constraint:
                        hard_failed_cnt += 1

                    req_match_rec = CandidateRequirementMatch(
                        organization_id=organization_id,
                        match_id=match_rec.id,
                        job_id=job_id,
                        job_requirement_id=req.id,
                        candidate_id=candidate_id,
                        requirement_type=req.requirement_type.name,
                        raw_required_value=req.raw_value,
                        canonical_required_value=req.canonical_value,
                        requirement_level=req.requirement_level.name,
                        hard_constraint=req.hard_constraint,
                        match_status=req_status,
                        candidate_value=cand_val,
                        normalized_candidate_value=norm_cand_val,
                        confidence=conf,
                        reason=reason,
                        evidence_text=ev_text,
                        evidence_verification_status=ev_v_status,
                    )
                    session.add(req_match_rec)

                # Stage 2: pgvector Semantic Context Matching
                match_rec.status = MatchProcessingStatusEnum.SEMANTIC_MATCHING
                sem_results = await SemanticMatcher.match_semantic_contexts(
                    session=session,
                    organization_id=organization_id,
                    job_id=job_id,
                    job_intelligence_version_id=job_intel_v.id,
                    candidate_id=candidate_id,
                    candidate_document_id=cand_doc.id,
                )

                for sem in sem_results:
                    sem_rec = CandidateSemanticMatch(
                        organization_id=organization_id,
                        match_id=match_rec.id,
                        job_id=job_id,
                        candidate_id=candidate_id,
                        query_context=sem["query_context"],
                        candidate_context=sem["candidate_context"],
                        similarity_score=sem["similarity_score"],
                        embedding_model=sem["embedding_model"],
                        dimension=sem["dimension"],
                    )
                    session.add(sem_rec)

                # Update Master Match Summary
                match_rec.status = MatchProcessingStatusEnum.COMPLETED
                match_rec.total_requirements_count = len(job_reqs)
                match_rec.matched_requirements_count = matched_cnt
                match_rec.hard_requirements_failed_count = hard_failed_cnt

                audit_rec = MatchProcessingAudit(
                    organization_id=organization_id,
                    match_id=match_rec.id,
                    processing_stage="CANDIDATE_FEATURE_MATCHING",
                    provider="SYSTEM_HYBRID",
                    model_name=settings.EMBEDDING_MODEL,
                    input_tokens=150,
                    output_tokens=150,
                    estimated_cost=0.0001,
                    latency_ms=120.0,
                )
                session.add(audit_rec)

                audit_log = AuditLog(
                    organization_id=organization_id,
                    user_id=user_id,
                    action="candidate.matching_processed",
                    resource_type="candidate_job_match",
                    resource_id=str(match_rec.id),
                )
                session.add(audit_log)

                await session.commit()

                event_envelope = EventEnvelope(
                    event_type="candidate.matching.completed",
                    aggregate_id=job_id,
                    organization_id=organization_id,
                    correlation_id=str(uuid.uuid4()),
                    payload={
                        "job_id": str(job_id),
                        "candidate_id": str(candidate_id),
                        "match_id": str(match_rec.id),
                        "status": "COMPLETED",
                    },
                )
                await event_bus.publish(event_envelope)

                logger.info(f"Successfully processed candidate matching features for job_id={job_id}, candidate_id={candidate_id}")
                return True

            except Exception as e:
                logger.error(f"Error processing candidate matching features: {e!s}")
                raise



