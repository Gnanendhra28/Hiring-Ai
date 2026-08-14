import time
import uuid
from typing import Optional
from sqlalchemy import select, func

from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.audit.models import AuditLog
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
)
from app.domains.ranking.models import (
    CandidateJobRanking,
    CandidateRankingVersion,
    RankingProcessingAudit,
    RankingVersionStatusEnum,
)
from app.domains.scoring.models import (
    CandidateHardRequirementResult,
    CandidateJobScore,
    EligibilityStatusEnum,
    ScoringConfiguration,
)
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus
from app.infrastructure.ranking.ranking_engine import RankingEngine

event_bus = InMemoryEventBus()

class RankingService:
    """
    Deterministic Candidate Ranking & Top-K Selection Engine Service.
    
    CRITICAL AI GOVERNANCE RULE:
    Zero LLM involvement in ranking or score calculations.
    Authoritative score originates strictly from Phase 9B CandidateJobScore.
    Contains ZERO automated application status mutation logic.
    """

    async def generate_ranking_snapshot(
        self,
        job_id: uuid.UUID,
        organization_id: uuid.UUID,
        top_k: int = 10,
        user_id: Optional[uuid.UUID] = None,
    ) -> Optional[CandidateRankingVersion]:
        logger.info(f"Starting deterministic ranking generation for job_id={job_id}, top_k={top_k} under org_id={organization_id}")
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
                return None

            if job_intel_v.status == JobIntelligenceVersionStatusEnum.STALE:
                logger.error(f"Active job intelligence version {job_intel_v.version_number} for job {job_id} is STALE. Regeneration required before ranking.")
                return None

            # 2. Fetch Active Scoring Configuration
            stmt_config = select(ScoringConfiguration).where(
                ScoringConfiguration.organization_id == organization_id,
                ScoringConfiguration.is_active.is_(True),
            ).order_by(ScoringConfiguration.version_number.desc())
            config = (await session.execute(stmt_config)).scalars().first()

            if not config:
                logger.error(f"No active scoring configuration found for organization {organization_id}.")
                return None

            # 3. Fetch Compatible Phase 9B Scores for Job & Version Consistency Check
            stmt_scores = select(CandidateJobScore).where(
                CandidateJobScore.job_id == job_id,
                CandidateJobScore.organization_id == organization_id,
                CandidateJobScore.job_intelligence_version_id == job_intel_v.id,
                CandidateJobScore.scoring_configuration_id == config.id,
            )
            scores = list((await session.execute(stmt_scores)).scalars().all())

            if not scores:
                logger.warning(f"No Phase 9B candidate score records found for job {job_id}. Execute Phase 9B scoring first.")
                # Create empty ranking snapshot
                ver_num_stmt = select(func.coalesce(func.max(CandidateRankingVersion.ranking_version), 0)).where(
                    CandidateRankingVersion.job_id == job_id,
                    CandidateRankingVersion.organization_id == organization_id,
                )
                next_version = (await session.execute(ver_num_stmt)).scalar() + 1

                ranking_v = CandidateRankingVersion(
                    organization_id=organization_id,
                    job_id=job_id,
                    job_intelligence_version_id=job_intel_v.id,
                    scoring_configuration_id=config.id,
                    ranking_version=next_version,
                    top_k=top_k,
                    status=RankingVersionStatusEnum.COMPLETED,
                    candidate_count=0,
                    eligible_candidate_count=0,
                    ineligible_candidate_count=0,
                    unknown_candidate_count=0,
                    created_by_user_id=user_id,
                )
                session.add(ranking_v)
                await session.commit()
                return ranking_v

            # 4. Prepare Score Metadata Items for Tie-Breaker Engine
            candidate_score_items = []
            for s in scores:
                # Count failed hard requirements
                stmt_failed = select(func.count(CandidateHardRequirementResult.id)).where(
                    CandidateHardRequirementResult.candidate_job_score_id == s.id,
                    CandidateHardRequirementResult.status == "NOT_MATCHED",
                )
                failed_count = (await session.execute(stmt_failed)).scalar() or 0

                # Count matched requirements
                stmt_matched = select(func.count(CandidateHardRequirementResult.id)).where(
                    CandidateHardRequirementResult.candidate_job_score_id == s.id,
                    CandidateHardRequirementResult.status == "MATCHED",
                )
                matched_count = (await session.execute(stmt_matched)).scalar() or 0

                candidate_score_items.append({
                    "candidate_job_score": s,
                    "candidate_job_score_id": s.id,
                    "candidate_id": s.candidate_id,
                    "application_id": s.application_id,
                    "candidate_document_id": s.candidate_document_id,
                    "score": s.overall_score,
                    "score_confidence": s.score_confidence,
                    "eligibility_status": s.eligibility_status,
                    "failed_hard_reqs_count": failed_count,
                    "matched_reqs_count": matched_count,
                    "created_at": s.created_at,
                })

            # 5. Execute Deterministic Ranking Engine
            ranked_results = RankingEngine.rank_candidates(
                candidate_scores=candidate_score_items,
                top_k=top_k,
            )

            # 6. Increment Version Number & Create Version Snapshot
            ver_num_stmt = select(func.coalesce(func.max(CandidateRankingVersion.ranking_version), 0)).where(
                CandidateRankingVersion.job_id == job_id,
                CandidateRankingVersion.organization_id == organization_id,
            )
            next_version = (await session.execute(ver_num_stmt)).scalar() + 1

            eligible_cnt = sum(1 for r in ranked_results if r["eligibility_status"] == EligibilityStatusEnum.PASS)
            ineligible_cnt = sum(1 for r in ranked_results if r["eligibility_status"] == EligibilityStatusEnum.FAIL)
            unknown_cnt = sum(1 for r in ranked_results if r["eligibility_status"] == EligibilityStatusEnum.UNKNOWN)

            ranking_v = CandidateRankingVersion(
                organization_id=organization_id,
                job_id=job_id,
                job_intelligence_version_id=job_intel_v.id,
                scoring_configuration_id=config.id,
                ranking_version=next_version,
                top_k=top_k,
                status=RankingVersionStatusEnum.COMPLETED,
                candidate_count=len(ranked_results),
                eligible_candidate_count=eligible_cnt,
                ineligible_candidate_count=ineligible_cnt,
                unknown_candidate_count=unknown_cnt,
                created_by_user_id=user_id,
            )
            session.add(ranking_v)
            await session.flush()

            # 7. Bulk Persist Candidate Job Ranking Results
            for r_item in ranked_results:
                r_obj = CandidateJobRanking(
                    organization_id=organization_id,
                    ranking_version_id=ranking_v.id,
                    job_id=job_id,
                    candidate_id=r_item["candidate_id"],
                    application_id=r_item["application_id"],
                    candidate_job_score_id=r_item["candidate_job_score_id"],
                    candidate_document_id=r_item["candidate_document_id"],
                    job_intelligence_version_id=job_intel_v.id,
                    rank_position=r_item["rank_position"],
                    is_top_k=r_item["is_top_k"],
                    eligibility_status=r_item["eligibility_status"],
                    score=r_item["score"],
                    score_confidence=r_item["score_confidence"],
                )
                session.add(r_obj)

            duration_ms = (time.time() - start_time) * 1000.0
            audit_rec = RankingProcessingAudit(
                organization_id=organization_id,
                ranking_version_id=ranking_v.id,
                processing_duration_ms=duration_ms,
                status="COMPLETED",
            )
            session.add(audit_rec)

            audit_log = AuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action="candidate.ranking_generated",
                resource_type="candidate_ranking_version",
                resource_id=str(ranking_v.id),
            )
            session.add(audit_log)

            await session.commit()

            # Publish Event
            event_envelope = EventEnvelope(
                event_type="candidate.ranking.completed",
                aggregate_id=job_id,
                organization_id=organization_id,
                correlation_id=str(uuid.uuid4()),
                payload={
                    "job_id": str(job_id),
                    "ranking_version_id": str(ranking_v.id),
                    "ranking_version": next_version,
                    "top_k": top_k,
                    "candidate_count": len(ranked_results),
                    "eligible_candidate_count": eligible_cnt,
                },
            )
            await event_bus.publish(event_envelope)

            logger.info(f"Successfully generated candidate ranking version {next_version} for job {job_id} with {len(ranked_results)} candidates.")
            return ranking_v
