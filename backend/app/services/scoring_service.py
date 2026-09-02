import time
import uuid
from sqlalchemy import delete, select

from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
)
from app.domains.matching.models import (
    CandidateJobMatch,
    CandidateRequirementMatch,
    CandidateSemanticMatch,
)
from app.domains.scoring.models import (
    CandidateFactorScore,
    CandidateHardRequirementResult,
    CandidateJobScore,
    ScoringConfiguration,
    ScoringProcessingAudit,
    ScoringProcessingStatusEnum,
)
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus
from app.infrastructure.scoring.scoring_engine import ScoringEngine

event_bus = InMemoryEventBus()

class ScoringService:
    """
    Deterministic Candidate Scoring Engine Service.
    Calculates overall score (0-100), factor scores, eligibility, and confidence.
    
    CRITICAL AI GOVERNANCE RULE:
    Contains ZERO LLM-generated scores, candidate rankings, or automatic state mutations.
    """

    async def get_or_create_active_configuration(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> ScoringConfiguration:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id, user_id=user_id)

            stmt = select(ScoringConfiguration).where(
                ScoringConfiguration.organization_id == organization_id,
                ScoringConfiguration.is_active.is_(True),
            ).order_by(ScoringConfiguration.version_number.desc())

            config = (await session.execute(stmt)).scalars().first()

            if not config:
                config = ScoringConfiguration(
                    organization_id=organization_id,
                    version_number=1,
                    is_active=True,
                    required_skills_weight=0.30,
                    semantic_match_weight=0.20,
                    experience_weight=0.20,
                    education_weight=0.10,
                    preferred_skills_weight=0.10,
                    other_requirements_weight=0.10,
                    created_by_user_id=user_id,
                )
                session.add(config)
                await session.commit()
                await session.refresh(config)

            return config

    async def process_candidate_scoring(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        application_id: uuid.UUID | None = None,
    ) -> bool:
        logger.info(f"Starting deterministic candidate scoring for job_id={job_id}, candidate_id={candidate_id} under org_id={organization_id}")
        start_time = time.time()

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
                logger.error(f"Active job intelligence version {job_intel_v.version_number} for job {job_id} is STALE. Regeneration required before scoring.")
                return False

            # 2. Fetch Active Scoring Configuration
            stmt_config = select(ScoringConfiguration).where(
                ScoringConfiguration.organization_id == organization_id,
                ScoringConfiguration.is_active.is_(True),
            ).order_by(ScoringConfiguration.version_number.desc())
            config = (await session.execute(stmt_config)).scalars().first()

            if not config:
                config = ScoringConfiguration(
                    organization_id=organization_id,
                    version_number=1,
                    is_active=True,
                    required_skills_weight=0.30,
                    semantic_match_weight=0.20,
                    experience_weight=0.20,
                    education_weight=0.10,
                    preferred_skills_weight=0.10,
                    other_requirements_weight=0.10,
                    created_by_user_id=user_id,
                )
                session.add(config)
                await session.flush()

            if not ScoringEngine.validate_weights(config):
                logger.error(f"Invalid scoring configuration weights for version {config.version_number}.")
                return False

            # 3. Fetch Master Candidate Job Match Record & Feature Matches from Phase 9A
            stmt_match = select(CandidateJobMatch).where(
                CandidateJobMatch.job_id == job_id,
                CandidateJobMatch.candidate_id == candidate_id,
                CandidateJobMatch.job_intelligence_version_id == job_intel_v.id,
                CandidateJobMatch.organization_id == organization_id,
            ).order_by(CandidateJobMatch.created_at.desc())
            match_rec = (await session.execute(stmt_match)).scalars().first()

            if not match_rec:
                logger.info(f"No CandidateJobMatch record found for job {job_id} and candidate {candidate_id}. Executing Phase 9A feature matching.")
                from app.services.matching_service import MatchingService
                matching_service = MatchingService()
                match_success = await matching_service.process_candidate_matching(
                    job_id=job_id,
                    candidate_id=candidate_id,
                    organization_id=organization_id,
                    user_id=user_id,
                    application_id=application_id,
                )
                if not match_success:
                    logger.error(f"Candidate feature matching failed for job {job_id} and candidate {candidate_id}.")
                    return False

                match_rec = (await session.execute(stmt_match)).scalars().first()
                if not match_rec:
                    logger.error(f"CandidateJobMatch record missing after matching execution for job {job_id} and candidate {candidate_id}.")
                    return False

            stmt_reqs = select(CandidateRequirementMatch).where(CandidateRequirementMatch.match_id == match_rec.id)
            req_matches = list((await session.execute(stmt_reqs)).scalars().all())

            stmt_sems = select(CandidateSemanticMatch).where(CandidateSemanticMatch.match_id == match_rec.id)
            sem_matches = list((await session.execute(stmt_sems)).scalars().all())

            # 4. Calculate Deterministic Candidate Score
            score_data = ScoringEngine.calculate_candidate_score(
                config=config,
                req_matches=req_matches,
                sem_matches=sem_matches,
            )

            # 5. Idempotent Persistence — Delete prior score record for this exact version tuple
            stmt_prev = select(CandidateJobScore).where(
                CandidateJobScore.job_id == job_id,
                CandidateJobScore.candidate_id == candidate_id,
                CandidateJobScore.job_intelligence_version_id == job_intel_v.id,
                CandidateJobScore.candidate_document_id == match_rec.candidate_document_id,
                CandidateJobScore.scoring_configuration_version == config.version_number,
            )
            prev_score = (await session.execute(stmt_prev)).scalar_one_or_none()

            if prev_score:
                await session.execute(delete(CandidateFactorScore).where(CandidateFactorScore.candidate_job_score_id == prev_score.id))
                await session.execute(delete(CandidateHardRequirementResult).where(CandidateHardRequirementResult.candidate_job_score_id == prev_score.id))
                await session.execute(delete(ScoringProcessingAudit).where(ScoringProcessingAudit.candidate_job_score_id == prev_score.id))
                await session.delete(prev_score)
                await session.flush()

            # Create Master Score Record
            score_rec = CandidateJobScore(
                organization_id=organization_id,
                job_id=job_id,
                job_intelligence_version_id=job_intel_v.id,
                candidate_id=candidate_id,
                candidate_document_id=match_rec.candidate_document_id,
                application_id=application_id or match_rec.application_id,
                scoring_configuration_id=config.id,
                scoring_configuration_version=config.version_number,
                eligibility_status=score_data["eligibility_status"],
                overall_score=score_data["overall_score"],
                score_confidence=score_data["score_confidence"],
                confidence_tier=score_data["confidence_tier"],
                status=ScoringProcessingStatusEnum.COMPLETED,
            )
            session.add(score_rec)
            await session.flush()

            # Persist Granular Factor Scores
            for f_data in score_data["factor_scores"]:
                f_rec = CandidateFactorScore(
                    organization_id=organization_id,
                    candidate_job_score_id=score_rec.id,
                    factor_type=f_data["factor_type"],
                    raw_score=f_data["raw_score"],
                    normalized_score=f_data["normalized_score"],
                    configured_weight=f_data["configured_weight"],
                    normalized_weight=f_data["normalized_weight"],
                    weighted_contribution=f_data["weighted_contribution"],
                    applicable=f_data["applicable"],
                    reason=f_data["reason"],
                    confidence=f_data["confidence"],
                )
                session.add(f_rec)

            # Persist Hard Requirement Results
            for hr_data in score_data["hard_requirement_results"]:
                hr_rec = CandidateHardRequirementResult(
                    organization_id=organization_id,
                    candidate_job_score_id=score_rec.id,
                    requirement_id=hr_data["requirement_id"],
                    status=hr_data["status"],
                    candidate_value=hr_data["candidate_value"],
                    required_value=hr_data["required_value"],
                    operator=hr_data["operator"],
                    reason=hr_data["reason"],
                    confidence=hr_data["confidence"],
                    evidence_text=hr_data["evidence_text"],
                )
                session.add(hr_rec)

            duration_ms = (time.time() - start_time) * 1000.0
            audit_rec = ScoringProcessingAudit(
                organization_id=organization_id,
                candidate_job_score_id=score_rec.id,
                processing_duration_ms=duration_ms,
                status="COMPLETED",
            )
            session.add(audit_rec)

            audit_log = AuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action="candidate.scoring_processed",
                resource_type="candidate_job_score",
                resource_id=str(score_rec.id),
            )
            session.add(audit_log)

            await session.commit()

            # Publish Scoring Event
            event_envelope = EventEnvelope(
                event_type="candidate.scoring.completed",
                aggregate_id=job_id,
                organization_id=organization_id,
                correlation_id=str(uuid.uuid4()),
                payload={
                    "job_id": str(job_id),
                    "candidate_id": str(candidate_id),
                    "score_id": str(score_rec.id),
                    "overall_score": score_data["overall_score"],
                    "eligibility_status": score_data["eligibility_status"].value,
                },
            )
            await event_bus.publish(event_envelope)

            logger.info(f"Successfully calculated deterministic score={score_data['overall_score']} for job_id={job_id}, candidate_id={candidate_id}")
            return True
