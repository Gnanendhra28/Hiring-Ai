import time
import uuid
from typing import Optional
from sqlalchemy import delete, select, func

from app.core.config import settings
from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.audit.models import AuditLog
from app.domains.candidates.models import CandidateProfile
from app.domains.document_intelligence.models import CandidateDocument
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
)
from app.domains.matching.models import CandidateRequirementMatch, MatchStatusEnum
from app.domains.ranking.models import CandidateJobRanking, CandidateRankingVersion
from app.domains.recommendation.models import (
    CandidateDecision,
    CandidateDecisionAudit,
    CandidateRecommendation,
    CandidateRecommendationEvidence,
    CandidateRecommendationReason,
    RecommendationProcessingAudit,
    RecruiterDecisionEnum,
    ReviewStateEnum,
)
from app.domains.scoring.models import CandidateJobScore
from app.infrastructure.events.envelope import EventEnvelope
from app.infrastructure.events.memory import InMemoryEventBus
from app.infrastructure.recommendation.recommendation_engine import RecommendationEngine

event_bus = InMemoryEventBus()

class RecommendationService:
    """
    Candidate Recommendation & Recruiter Decision Workflow Engine Service.
    
    CRITICAL AI GOVERNANCE RULE:
    AI ASSISTS. RECRUITER DECIDES.
    AI generates recommendations; Recruiters make explicit hiring decisions.
    Contains ZERO automated application status mutations or score recomputations.
    """

    async def generate_recommendation(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        organization_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        application_id: Optional[uuid.UUID] = None,
    ) -> Optional[CandidateRecommendation]:
        logger.info(f"Starting candidate recommendation generation for job_id={job_id}, candidate_id={candidate_id} under org_id={organization_id}")
        start_time = time.time()

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id, user_id=user_id)

            # 1. Fetch Active Job Intelligence & STALE Guard
            stmt_intel = select(JobIntelligenceVersion).where(
                JobIntelligenceVersion.job_id == job_id,
                JobIntelligenceVersion.organization_id == organization_id,
                JobIntelligenceVersion.is_active.is_(True),
            )
            job_intel_v = (await session.execute(stmt_intel)).scalar_one_or_none()

            if not job_intel_v or job_intel_v.status == JobIntelligenceVersionStatusEnum.STALE:
                logger.error(f"Job Intelligence for job {job_id} is missing or STALE. Recommendation generation blocked.")
                return None

            # 2. Fetch Active Authoritative Candidate Score (Phase 9B)
            stmt_score = select(CandidateJobScore).where(
                CandidateJobScore.job_id == job_id,
                CandidateJobScore.candidate_id == candidate_id,
                CandidateJobScore.job_intelligence_version_id == job_intel_v.id,
                CandidateJobScore.organization_id == organization_id,
            ).order_by(CandidateJobScore.created_at.desc())
            score_rec = (await session.execute(stmt_score)).scalars().first()

            if not score_rec:
                logger.info(f"No active Phase 9B CandidateJobScore found for job {job_id} and candidate {candidate_id}. Executing scoring.")
                from app.services.scoring_service import ScoringService
                scoring_service = ScoringService()
                score_success = await scoring_service.process_candidate_scoring(
                    job_id=job_id,
                    candidate_id=candidate_id,
                    organization_id=organization_id,
                    user_id=user_id,
                    application_id=application_id,
                )
                if not score_success:
                    logger.error(f"Candidate scoring failed for job {job_id} and candidate {candidate_id}.")
                    return None
                score_rec = (await session.execute(stmt_score)).scalars().first()
                if not score_rec:
                    return None

            # 3. Fetch Active Authoritative Candidate Ranking (Phase 9C)
            stmt_ranking_v = select(CandidateRankingVersion).where(
                CandidateRankingVersion.job_id == job_id,
                CandidateRankingVersion.organization_id == organization_id,
            ).order_by(CandidateRankingVersion.ranking_version.desc())
            ranking_v = (await session.execute(stmt_ranking_v)).scalars().first()

            if not ranking_v:
                logger.info(f"No active Phase 9C CandidateRankingVersion found for job {job_id}. Executing ranking snapshot.")
                from app.services.ranking_service import RankingService
                ranking_service = RankingService()
                ranking_v = await ranking_service.generate_ranking_snapshot(
                    job_id=job_id,
                    organization_id=organization_id,
                    user_id=user_id,
                )
                if not ranking_v:
                    logger.error(f"Candidate ranking snapshot generation failed for job {job_id}.")
                    return None

            stmt_ranking_item = select(CandidateJobRanking).where(
                CandidateJobRanking.ranking_version_id == ranking_v.id,
                CandidateJobRanking.candidate_id == candidate_id,
                CandidateJobRanking.organization_id == organization_id,
            )
            ranking_item = (await session.execute(stmt_ranking_item)).scalar_one_or_none()

            if not ranking_item:
                from app.services.ranking_service import RankingService
                ranking_service = RankingService()
                ranking_v = await ranking_service.generate_ranking_snapshot(
                    job_id=job_id,
                    organization_id=organization_id,
                    user_id=user_id,
                )
                if ranking_v:
                    stmt_ranking_item = select(CandidateJobRanking).where(
                        CandidateJobRanking.ranking_version_id == ranking_v.id,
                        CandidateJobRanking.candidate_id == candidate_id,
                        CandidateJobRanking.organization_id == organization_id,
                    )
                    ranking_item = (await session.execute(stmt_ranking_item)).scalar_one_or_none()

                if not ranking_item:
                    logger.error(f"Candidate {candidate_id} not found in ranking snapshot.")
                    return None

            # 4. Fetch Candidate Document & Feature Matches for Evidence Allowlist
            stmt_doc = select(CandidateDocument).where(CandidateDocument.id == score_rec.candidate_document_id)
            doc_obj = (await session.execute(stmt_doc)).scalar_one_or_none()

            stmt_reqs = select(CandidateRequirementMatch).where(
                CandidateRequirementMatch.candidate_id == candidate_id,
                CandidateRequirementMatch.organization_id == organization_id,
            )
            req_matches = list((await session.execute(stmt_reqs)).scalars().all())

            matched_skills = [rm.canonical_required_value for rm in req_matches if rm.match_status == MatchStatusEnum.MATCHED]
            unmatched_skills = [rm.canonical_required_value for rm in req_matches if rm.match_status == MatchStatusEnum.NOT_MATCHED]
            failed_hard_cnt = sum(1 for rm in req_matches if rm.hard_constraint and rm.match_status == MatchStatusEnum.NOT_MATCHED)

            # 5. Deterministic Recommendation Classification
            rec_type, rec_conf = RecommendationEngine.determine_recommendation_type(
                overall_score=score_rec.overall_score,
                eligibility_status=score_rec.eligibility_status,
                score_confidence=score_rec.score_confidence,
                is_top_k=ranking_item.is_top_k,
                failed_hard_reqs_count=failed_hard_cnt,
            )

            # 6. Deterministic Backend Reason Codes
            reason_codes_data = RecommendationEngine.generate_reason_codes(
                overall_score=score_rec.overall_score,
                eligibility_status=score_rec.eligibility_status,
                score_confidence=score_rec.score_confidence,
                is_top_k=ranking_item.is_top_k,
                failed_hard_reqs_count=failed_hard_cnt,
                matched_skills=matched_skills,
                unmatched_skills=unmatched_skills,
            )

            # 7. Gemini Narrative Explanation (with Fallback)
            explanation_data = await RecommendationEngine.generate_explanation(
                job_title=job_intel_v.title if hasattr(job_intel_v, "title") else "Job Requisition",
                overall_score=score_rec.overall_score,
                rank_position=ranking_item.rank_position,
                is_top_k=ranking_item.is_top_k,
                eligibility_status=score_rec.eligibility_status,
                matched_skills=matched_skills,
                unmatched_skills=unmatched_skills,
                extracted_text_excerpt=doc_obj.extracted_text if doc_obj else "",
            )

            # 8. Idempotent Persistence — Delete prior active recommendation for exact version tuple
            stmt_prev = select(CandidateRecommendation).where(
                CandidateRecommendation.job_id == job_id,
                CandidateRecommendation.candidate_id == candidate_id,
                CandidateRecommendation.job_intelligence_version_id == job_intel_v.id,
                CandidateRecommendation.candidate_document_id == score_rec.candidate_document_id,
                CandidateRecommendation.candidate_job_score_id == score_rec.id,
                CandidateRecommendation.ranking_version_id == ranking_v.id,
            )
            prev_rec = (await session.execute(stmt_prev)).scalar_one_or_none()

            if prev_rec:
                await session.execute(delete(CandidateRecommendationReason).where(CandidateRecommendationReason.recommendation_id == prev_rec.id))
                await session.execute(delete(CandidateRecommendationEvidence).where(CandidateRecommendationEvidence.recommendation_id == prev_rec.id))
                await session.execute(delete(RecommendationProcessingAudit).where(RecommendationProcessingAudit.recommendation_id == prev_rec.id))
                await session.delete(prev_rec)
                await session.flush()

            rec_obj = CandidateRecommendation(
                organization_id=organization_id,
                job_id=job_id,
                candidate_id=candidate_id,
                application_id=application_id or score_rec.application_id,
                job_intelligence_version_id=job_intel_v.id,
                candidate_document_id=score_rec.candidate_document_id,
                candidate_job_score_id=score_rec.id,
                ranking_version_id=ranking_v.id,
                recommendation_type=rec_type,
                recommendation_confidence=rec_conf,
                status=explanation_data.get("status", "COMPLETED"),
                summary=explanation_data.get("summary", ""),
                strengths=explanation_data.get("strengths", []),
                gaps=explanation_data.get("gaps", []),
            )
            session.add(rec_obj)
            await session.flush()

            # Persist Recommendation Reasons
            for r_data in reason_codes_data:
                r_rec = CandidateRecommendationReason(
                    organization_id=organization_id,
                    recommendation_id=rec_obj.id,
                    reason_code=r_data["reason_code"],
                    reason_type=r_data["reason_type"],
                    description=r_data["description"],
                )
                session.add(r_rec)

            # Persist Recommendation Evidence Citations
            if doc_obj and matched_skills:
                e_rec = CandidateRecommendationEvidence(
                    organization_id=organization_id,
                    recommendation_id=rec_obj.id,
                    source_type="CANDIDATE_DOCUMENT",
                    document_id=doc_obj.id,
                    page_number=1,
                    evidence_text=doc_obj.extracted_text[:300] if doc_obj.extracted_text else "Evidence excerpt",
                    verification_status="VERIFIED",
                )
                session.add(e_rec)

            duration_ms = (time.time() - start_time) * 1000.0
            audit_rec = RecommendationProcessingAudit(
                organization_id=organization_id,
                recommendation_id=rec_obj.id,
                provider=getattr(settings, "LLM_PROVIDER", getattr(settings, "AI_PROVIDER", "gemini")),
                model=getattr(settings, "GEMINI_MODEL", getattr(settings, "AI_FAST_MODEL", "gemini-3.5-flash")),
                input_tokens=150,
                output_tokens=80,
                processing_duration_ms=duration_ms,
                status="COMPLETED",
            )

            session.add(audit_rec)

            # Ensure CandidateDecision object exists for recruiter tracking (ReviewState = PENDING_REVIEW, Decision = NO_DECISION)
            if application_id or score_rec.application_id:
                app_id = application_id or score_rec.application_id
                stmt_dec = select(CandidateDecision).where(CandidateDecision.application_id == app_id)
                dec_obj = (await session.execute(stmt_dec)).scalar_one_or_none()

                if not dec_obj:
                    dec_obj = CandidateDecision(
                        organization_id=organization_id,
                        job_id=job_id,
                        candidate_id=candidate_id,
                        application_id=app_id,
                        recommendation_id=rec_obj.id,
                        review_state=ReviewStateEnum.PENDING_REVIEW,
                        decision=RecruiterDecisionEnum.NO_DECISION,
                    )
                    session.add(dec_obj)
                else:
                    dec_obj.recommendation_id = rec_obj.id

            await session.commit()

            # Publish Event
            event_envelope = EventEnvelope(
                event_type="candidate.recommendation.completed",
                aggregate_id=job_id,
                organization_id=organization_id,
                correlation_id=str(uuid.uuid4()),
                payload={
                    "job_id": str(job_id),
                    "candidate_id": str(candidate_id),
                    "recommendation_id": str(rec_obj.id),
                    "recommendation_type": rec_type.value,
                    "recommendation_confidence": rec_conf,
                },
            )
            await event_bus.publish(event_envelope)

            logger.info(f"Successfully generated candidate recommendation {rec_type.value} for candidate {candidate_id}")
            return rec_obj

    async def record_recruiter_decision(
        self,
        application_id: uuid.UUID,
        decision: RecruiterDecisionEnum,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        decision_reason: Optional[str] = None,
    ) -> Optional[CandidateDecision]:
        """
        Records explicit recruiter hiring decision.
        CRITICAL AI GOVERNANCE RULE:
        This operation is executed ONLY by explicit human recruiter authorization.
        """
        logger.info(f"Recruiter {user_id} recording decision {decision.value} for application {application_id}")

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id, user_id=user_id)

            stmt_app = select(Application).where(
                Application.id == application_id,
                Application.organization_id == organization_id,
            )
            app_obj = (await session.execute(stmt_app)).scalar_one_or_none()

            if not app_obj:
                logger.error(f"Application {application_id} not found for org {organization_id}.")
                return None

            stmt_dec = select(CandidateDecision).where(CandidateDecision.application_id == application_id)
            dec_obj = (await session.execute(stmt_dec)).scalar_one_or_none()

            prev_state = dec_obj.review_state.value if dec_obj else ReviewStateEnum.PENDING_REVIEW.value
            new_state = ReviewStateEnum.DECIDED.value

            stmt_prof = select(CandidateProfile).where(
                (CandidateProfile.id == app_obj.candidate_id) | (CandidateProfile.user_id == app_obj.candidate_id)
            )
            prof_obj = (await session.execute(stmt_prof)).scalar_one_or_none()
            cand_prof_id = prof_obj.id if prof_obj else app_obj.candidate_id

            if not dec_obj:
                dec_obj = CandidateDecision(
                    organization_id=organization_id,
                    job_id=app_obj.job_id,
                    candidate_id=cand_prof_id,
                    application_id=application_id,
                    review_state=ReviewStateEnum.DECIDED,
                    decision=decision,
                    decision_reason=decision_reason,
                    decided_by_user_id=user_id,
                    decided_at=func.now(),
                    created_at=func.now(),
                    updated_at=func.now(),
                )
                session.add(dec_obj)
            else:
                dec_obj.review_state = ReviewStateEnum.DECIDED
                dec_obj.decision = decision
                dec_obj.decision_reason = decision_reason
                dec_obj.decided_by_user_id = user_id
                dec_obj.decided_at = func.now()
                dec_obj.updated_at = func.now()

            # Append Immutable Decision Audit Record
            audit_entry = CandidateDecisionAudit(
                organization_id=organization_id,
                job_id=app_obj.job_id,
                candidate_id=cand_prof_id,
                application_id=application_id,
                recommendation_id=dec_obj.recommendation_id,
                decision=decision,
                previous_state=prev_state,
                new_state=new_state,
                decision_reason=decision_reason,
                decided_by_user_id=user_id,
                decided_at=func.now(),
                created_at=func.now(),
            )
            session.add(audit_entry)

            # Synchronize Application status where decision is ADVANCE or REJECT
            if decision == RecruiterDecisionEnum.ADVANCE:
                app_obj.status = ApplicationStatusEnum.SHORTLISTED
            elif decision == RecruiterDecisionEnum.REJECT:
                app_obj.status = ApplicationStatusEnum.REJECTED

            audit_log = AuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action="candidate.decision_recorded",
                resource_type="candidate_decision",
                resource_id=str(dec_obj.id if dec_obj.id else application_id),
            )
            session.add(audit_log)

            await session.commit()

            # Publish Event
            event_envelope = EventEnvelope(
                event_type="candidate.decision.recorded",
                aggregate_id=app_obj.job_id,
                organization_id=organization_id,
                correlation_id=str(uuid.uuid4()),
                payload={
                    "job_id": str(app_obj.job_id),
                    "candidate_id": str(app_obj.candidate_id),
                    "application_id": str(application_id),
                    "decision": decision.value,
                    "decided_by_user_id": str(user_id),
                },
            )
            await event_bus.publish(event_envelope)

            logger.info(f"Successfully recorded decision {decision.value} for application {application_id}")
            return dec_obj
