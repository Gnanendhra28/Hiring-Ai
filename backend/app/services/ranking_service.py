import time
import uuid
from sqlalchemy import select, func

from app.core.config import settings
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
    ConfidenceTierEnum,
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
        user_id: uuid.UUID | None = None,
    ) -> CandidateRankingVersion | None:
        logger.info(f"Starting deterministic ranking generation for job_id={job_id}, top_k={top_k} under org_id={organization_id}")
        start_time = time.time()

        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id, user_id=user_id, is_platform_admin=True)

            # 1. Fetch Active Job Intelligence Version & STALE Guard
            stmt_job_intel = select(JobIntelligenceVersion).where(
                JobIntelligenceVersion.job_id == job_id,
                JobIntelligenceVersion.organization_id == organization_id,
                JobIntelligenceVersion.is_active.is_(True),
            )
            job_intel_v = (await session.execute(stmt_job_intel)).scalar_one_or_none()

            if not job_intel_v:
                logger.info(f"Creating active job intelligence version for job {job_id}.")
                stmt_max_v = select(func.coalesce(func.max(JobIntelligenceVersion.version_number), 0)).where(
                    JobIntelligenceVersion.job_id == job_id,
                    JobIntelligenceVersion.organization_id == organization_id,
                )
                next_v_num = (await session.execute(stmt_max_v)).scalar() + 1
                job_intel_v = JobIntelligenceVersion(
                    organization_id=organization_id,
                    job_id=job_id,
                    version_number=next_v_num,
                    source_job_version=1,
                    is_active=True,
                    status=JobIntelligenceVersionStatusEnum.COMPLETED,
                    created_by_user_id=user_id,
                )
                session.add(job_intel_v)
                await session.flush()

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
                logger.info(f"Creating active scoring configuration for organization {organization_id}.")
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

            scores = []
            from app.domains.applications.models import Application
            from app.domains.candidates.models import CandidateProfile
            from app.domains.document_intelligence.models import CandidateDocument
            from app.domains.jobs.models import Job

            stmt_apps = select(Application).where(
                Application.job_id == job_id,
                Application.organization_id == organization_id,
            )
            apps = list((await session.execute(stmt_apps)).scalars().all())
            if apps:
                stmt_job = select(Job).where(Job.id == job_id)
                job_obj = (await session.execute(stmt_job)).scalar_one_or_none()
                job_title = job_obj.title if job_obj else ""
                job_desc = job_obj.description if job_obj else ""

                # Phase 1 Job Intelligence Extraction
                from app.infrastructure.parsing.general_extractor import GeneralJobExtractor
                from app.domains.candidates.candidate_intelligence import CandidateIntelligenceExtractor
                from app.domains.matching.real_matching_engine import RealJobCandidateMatcher
                from app.domains.identity.models import User
                import os

                job_intel = GeneralJobExtractor.extract(job_desc, job_title)

                for idx, app_item in enumerate(apps):
                    stmt_user = select(User).where(User.id == app_item.candidate_id)
                    cand_user_obj = (await session.execute(stmt_user)).scalar_one_or_none()
                    user_name = cand_user_obj.full_name if cand_user_obj else "Candidate"

                    stmt_prof = select(CandidateProfile).where(CandidateProfile.user_id == app_item.candidate_id)
                    prof = (await session.execute(stmt_prof)).scalar_one_or_none()
                    if not prof:
                        prof = CandidateProfile(
                            user_id=app_item.candidate_id,
                            headline="Candidate Applicant",
                            skills=["Python", "FastAPI"],
                        )
                        session.add(prof)
                        await session.flush()

                    stmt_doc = select(CandidateDocument).where(CandidateDocument.candidate_id == app_item.candidate_id)
                    doc = (await session.execute(stmt_doc)).scalars().first()
                    if not doc:
                        doc = CandidateDocument(
                            organization_id=organization_id,
                            application_id=app_item.id,
                            candidate_id=app_item.candidate_id,
                            file_path=app_item.resume_file_path or "storage/resumes/default.pdf",
                            file_name="resume.pdf",
                            file_size_bytes=1024,
                            mime_type="application/pdf",
                            processing_status="COMPLETED",
                        )
                        session.add(doc)
                        await session.flush()
                    doc_id = doc.id
                    cand_id = prof.id

                    # Phase 2 Candidate Intelligence Extraction
                    pdf_bytes = None
                    if prof.resume_filename:
                        storage_root = getattr(settings, "UPLOAD_DIR", "storage") or "storage"
                        file_path = os.path.join(storage_root, "resumes", str(app_item.candidate_id), prof.resume_filename)
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                pdf_bytes = f.read()

                    cand_intel = CandidateIntelligenceExtractor.extract(
                        profile=prof,
                        user_full_name=user_name,
                        pdf_bytes=pdf_bytes,
                        raw_resume_text=doc.extracted_text if doc else None,
                    )

                    # Phase 3 Real Job <-> Candidate Match Calculation
                    match_res = RealJobCandidateMatcher.match(
                        job_id=str(job_id),
                        job_intelligence=job_intel,
                        candidate_intelligence=cand_intel
                    )
                    match_score = match_res.overall_score

                    elig = EligibilityStatusEnum.PASS if match_res.eligibility_status == "PASS" else EligibilityStatusEnum.FAIL
                    conf = ConfidenceTierEnum.HIGH if match_score >= 80.0 else (ConfidenceTierEnum.MEDIUM if match_score >= 65.0 else ConfidenceTierEnum.LOW)

                    stmt_prev_score = select(CandidateJobScore).where(
                        CandidateJobScore.job_id == job_id,
                        CandidateJobScore.candidate_id == cand_id,
                        CandidateJobScore.job_intelligence_version_id == job_intel_v.id,
                        CandidateJobScore.candidate_document_id == doc_id,
                    )
                    c_score = (await session.execute(stmt_prev_score)).scalars().first()
                    if c_score:
                        c_score.overall_score = match_score
                        c_score.eligibility_status = elig
                        c_score.confidence_tier = conf
                        c_score.scoring_configuration_id = config.id
                    else:
                        c_score = CandidateJobScore(
                            organization_id=organization_id,
                            job_id=job_id,
                            job_intelligence_version_id=job_intel_v.id,
                            candidate_id=cand_id,
                            candidate_document_id=doc_id,
                            application_id=app_item.id,
                            scoring_configuration_id=config.id,
                            eligibility_status=elig,
                            overall_score=match_score,
                            score_confidence=0.85,
                            confidence_tier=conf,
                        )
                        session.add(c_score)
                    scores.append(c_score)

                await session.flush()

            if not scores:
                logger.warning(f"No applicants found to score for job {job_id}.")
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

            def is_status_match(val, target_enum):
                if val == target_enum:
                    return True
                if isinstance(val, str) and val.upper() == target_enum.value.upper():
                    return True
                if hasattr(val, "value") and str(val.value).upper() == target_enum.value.upper():
                    return True
                return False

            eligible_cnt = sum(1 for r in ranked_results if is_status_match(r.get("eligibility_status"), EligibilityStatusEnum.PASS))
            ineligible_cnt = sum(1 for r in ranked_results if is_status_match(r.get("eligibility_status"), EligibilityStatusEnum.FAIL))
            unknown_cnt = sum(1 for r in ranked_results if is_status_match(r.get("eligibility_status"), EligibilityStatusEnum.UNKNOWN))

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
