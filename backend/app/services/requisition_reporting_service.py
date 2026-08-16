import csv
import io
import statistics
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import func, select

from app.core.logging import logger
from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application, ApplicationStatusEnum, CandidatePlacement, OfferStatusEnum
from app.domains.identity.models import User
from app.domains.organizations.models import OrganizationMembership
from app.domains.job_intelligence.models import JobIntelligenceVersion, JobIntelligenceVersionStatusEnum
from app.domains.jobs.models import Job, JobStatusEnum
from app.domains.ranking.models import CandidateJobRanking
from app.domains.recommendation.models import (
    CandidateDecision,
    CandidateDecisionAudit,
    CandidateRecommendation,
    RecruiterDecisionEnum,
    ReviewStateEnum,
)
from app.domains.scoring.models import CandidateJobScore
from app.domains.requisitions.schemas import (
    DecisionAnalytics,
    FunnelConversionMetrics,
    OfferAnalytics,
    RequisitionReportResponse,
    ScoreAnalytics,
    TenantRequisitionReportResponse,
)

class RequisitionReportingService:
    """
    Enterprise Requisition Reporting & Analytics Service.
    All calculations are 100% deterministic SQL / Python aggregations.
    0 LLM involvement in metrics calculation.
    Enforces organization_id RLS tenant isolation.
    """

    async def get_requisition_report(
        self, job_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[RequisitionReportResponse]:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            # 1. Fetch Job
            stmt_job = select(Job).where(
                Job.id == job_id,
                Job.organization_id == organization_id,
            )
            job_obj = (await session.execute(stmt_job)).scalar_one_or_none()
            if not job_obj:
                return None

            # 2. Fetch Active Job Intelligence Version
            stmt_intel = (
                select(JobIntelligenceVersion)
                .where(
                    JobIntelligenceVersion.job_id == job_id,
                    JobIntelligenceVersion.organization_id == organization_id,
                    JobIntelligenceVersion.is_active == True,
                )
                .order_by(JobIntelligenceVersion.version_number.desc())
                .limit(1)
            )
            intel_obj = (await session.execute(stmt_intel)).scalar_one_or_none()

            # 3. Application Pipeline Counts
            stmt_apps = select(Application).where(
                Application.job_id == job_id,
                Application.organization_id == organization_id,
            )
            apps = list((await session.execute(stmt_apps)).scalars().all())
            total_apps = len(apps)

            # 4. Scores & Eligibility Analytics
            stmt_scores = select(CandidateJobScore).where(
                CandidateJobScore.job_id == job_id,
                CandidateJobScore.organization_id == organization_id,
            )
            scores = list((await session.execute(stmt_scores)).scalars().all())

            score_vals = [s.overall_score for s in scores if s.overall_score is not None]
            avg_score = round(float(statistics.mean(score_vals)), 2) if score_vals else None
            median_score = round(float(statistics.median(score_vals)), 2) if score_vals else None
            highest_score = round(float(max(score_vals)), 2) if score_vals else None
            lowest_score = round(float(min(score_vals)), 2) if score_vals else None

            pass_count = sum(1 for s in scores if getattr(s.eligibility_status, "value", s.eligibility_status) == "PASS")
            fail_count = sum(1 for s in scores if getattr(s.eligibility_status, "value", s.eligibility_status) == "FAIL")

            conf_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for s in scores:
                tier_val = getattr(s.confidence_tier, "value", s.confidence_tier)
                if tier_val in conf_dist:
                    conf_dist[tier_val] += 1

            eligible_apps = pass_count if scores else sum(1 for a in apps if a.status != ApplicationStatusEnum.REJECTED)
            ineligible_apps = max(0, total_apps - eligible_apps)

            # 5. Top-K Candidates (Rankings)
            stmt_rankings = select(func.count(CandidateJobRanking.id)).where(
                CandidateJobRanking.job_id == job_id,
                CandidateJobRanking.organization_id == organization_id,
            )
            top_k_candidates = (await session.execute(stmt_rankings)).scalar() or 0

            # 6. Recruiter Decisions & Audits
            stmt_audits = select(CandidateDecisionAudit).where(
                CandidateDecisionAudit.job_id == job_id,
                CandidateDecisionAudit.organization_id == organization_id,
            )
            audits = list((await session.execute(stmt_audits)).scalars().all())

            stmt_decisions = select(CandidateDecision).where(
                CandidateDecision.job_id == job_id,
                CandidateDecision.organization_id == organization_id,
            )
            decisions = list((await session.execute(stmt_decisions)).scalars().all())

            reviewed_candidate_ids = {d.candidate_id for d in decisions if d.review_state == ReviewStateEnum.DECIDED}
            reviewed_candidate_ids.update({a.candidate_id for a in audits})
            candidates_reviewed = len(reviewed_candidate_ids)

            adv_count = sum(1 for d in decisions if d.decision == RecruiterDecisionEnum.ADVANCE)
            rej_count = sum(1 for d in decisions if d.decision == RecruiterDecisionEnum.REJECT)
            hold_count = sum(1 for d in decisions if d.decision == RecruiterDecisionEnum.HOLD)

            decision_counts = {"ADVANCE": adv_count, "REJECT": rej_count, "HOLD": hold_count}
            decision_rates_pct = {
                "advance_rate_pct": round((adv_count / candidates_reviewed * 100.0), 2) if candidates_reviewed > 0 else 0.0,
                "reject_rate_pct": round((rej_count / candidates_reviewed * 100.0), 2) if candidates_reviewed > 0 else 0.0,
                "hold_rate_pct": round((hold_count / candidates_reviewed * 100.0), 2) if candidates_reviewed > 0 else 0.0,
            }

            # 7. AI Recommendations & Override Statistics
            stmt_recs = select(CandidateRecommendation).where(
                CandidateRecommendation.job_id == job_id,
                CandidateRecommendation.organization_id == organization_id,
            )
            recs = list((await session.execute(stmt_recs)).scalars().all())

            ai_rec_dist = {"RECOMMEND": 0, "REQUIRES_REVIEW": 0, "DO_NOT_RECOMMEND": 0}
            rec_map = {}
            for r in recs:
                if r.recommendation_type in ai_rec_dist:
                    ai_rec_dist[r.recommendation_type] += 1
                rec_map[r.candidate_id] = r.recommendation_type

            agreed = 0
            overridden = 0
            for d in decisions:
                r_type = rec_map.get(d.candidate_id)
                if r_type:
                    if (r_type == "RECOMMEND" and d.decision == RecruiterDecisionEnum.ADVANCE) or \
                       (r_type == "DO_NOT_RECOMMEND" and d.decision == RecruiterDecisionEnum.REJECT):
                        agreed += 1
                    else:
                        overridden += 1

            total_sample = agreed + overridden
            override_rate = round((overridden / total_sample * 100.0), 2) if total_sample > 0 else 0.0

            # 8. Candidate Placements & Offers
            stmt_pl = select(CandidatePlacement).where(
                CandidatePlacement.job_id == job_id,
                CandidatePlacement.organization_id == organization_id,
            )
            placements = list((await session.execute(stmt_pl)).scalars().all())

            offers_ext = sum(1 for p in placements if p.offer_status in (OfferStatusEnum.OFFER_EXTENDED, OfferStatusEnum.OFFER_ACCEPTED, OfferStatusEnum.HIRED))
            offers_acc = sum(1 for p in placements if p.offer_status in (OfferStatusEnum.OFFER_ACCEPTED, OfferStatusEnum.HIRED))
            cands_hired = sum(1 for p in placements if p.offer_status == OfferStatusEnum.HIRED)

            acceptance_rate_pct = round((offers_acc / offers_ext * 100.0), 2) if offers_ext > 0 else 0.0

            # Offer to Acceptance duration
            acc_durations = []
            for p in placements:
                if p.offer_created_at and p.offer_accepted_at:
                    dur = (p.offer_accepted_at - p.offer_created_at).total_seconds() / 86400.0
                    if dur >= 0:
                        acc_durations.append(dur)
            avg_offer_acc_days = round(float(statistics.mean(acc_durations)), 2) if acc_durations else None

            # 9. Time Analytics
            first_cand_days = None
            if apps and job_obj.created_at:
                earliest_sub = min(a.submitted_at for a in apps if a.submitted_at)
                if earliest_sub:
                    first_cand_days = round(max(0.0, (earliest_sub - job_obj.created_at).total_seconds() / 86400.0), 2)

            first_review_days = None
            first_decision_days = None
            if audits and apps:
                earliest_sub = min(a.submitted_at for a in apps if a.submitted_at)
                earliest_audit = min(a.created_at for a in audits if a.created_at)
                if earliest_sub and earliest_audit:
                    first_review_days = round(max(0.0, (earliest_audit - earliest_sub).total_seconds() / 86400.0), 2)
                    first_decision_days = round(max(0.0, (earliest_audit - job_obj.created_at).total_seconds() / 86400.0), 2)

            time_to_fill = None
            time_to_hire = None
            placed_pl = next((p for p in placements if p.offer_status == OfferStatusEnum.HIRED and p.placed_at), None)
            if placed_pl:
                if job_obj.created_at:
                    time_to_fill = round(max(0.0, (placed_pl.placed_at - job_obj.created_at).total_seconds() / 86400.0), 2)
                app_placed = next((a for a in apps if a.id == placed_pl.application_id), None)
                if app_placed and app_placed.submitted_at:
                    time_to_hire = round(max(0.0, (placed_pl.placed_at - app_placed.submitted_at).total_seconds() / 86400.0), 2)

            req_fill_status = "FILLED" if (cands_hired > 0 or job_obj.status == JobStatusEnum.CLOSED) else "OPEN"

            # 10. Funnel Conversion Percentages
            funnel_conv = FunnelConversionMetrics(
                application_to_eligible_pct=round((eligible_apps / total_apps * 100.0), 2) if total_apps > 0 else 0.0,
                eligible_to_top_k_pct=round((top_k_candidates / eligible_apps * 100.0), 2) if eligible_apps > 0 else 0.0,
                top_k_to_reviewed_pct=round((candidates_reviewed / top_k_candidates * 100.0), 2) if top_k_candidates > 0 else 0.0,
                reviewed_to_advanced_pct=round((adv_count / candidates_reviewed * 100.0), 2) if candidates_reviewed > 0 else 0.0,
                advanced_to_offer_pct=round((offers_ext / adv_count * 100.0), 2) if adv_count > 0 else 0.0,
                offer_to_accepted_pct=acceptance_rate_pct,
                accepted_to_hired_pct=round((cands_hired / offers_acc * 100.0), 2) if offers_acc > 0 else 0.0,
            )

            decision_analytics = DecisionAnalytics(
                decision_counts=decision_counts,
                decision_rates_pct=decision_rates_pct,
                ai_recommendation_distribution=ai_rec_dist,
                ai_override_sample_size=total_sample,
                ai_agreed_count=agreed,
                ai_overridden_count=overridden,
                ai_override_rate_pct=override_rate,
            )

            score_analytics = ScoreAnalytics(
                average_score=avg_score,
                median_score=median_score,
                highest_score=highest_score,
                lowest_score=lowest_score,
                pass_count=pass_count,
                fail_count=fail_count,
                confidence_distribution=conf_dist,
            )

            offer_analytics = OfferAnalytics(
                offers_extended=offers_ext,
                offers_accepted=offers_acc,
                offer_acceptance_rate_pct=acceptance_rate_pct,
                avg_offer_to_acceptance_days=avg_offer_acc_days,
            )

            return RequisitionReportResponse(
                requisition_id=job_obj.id,
                organization_id=organization_id,
                title=job_obj.title,
                department=job_obj.department,
                location=job_obj.location,
                employment_type=job_obj.employment_type.value,
                job_status=job_obj.status.value,
                created_at=job_obj.created_at,
                closed_at=placed_pl.placed_at if placed_pl else None,
                active_intelligence_version=intel_obj.version_number if intel_obj else None,
                intelligence_status=intel_obj.status.value if intel_obj else None,
                intelligence_confidence=intel_obj.overall_confidence if intel_obj else None,
                total_applications=total_apps,
                eligible_applications=eligible_apps,
                ineligible_applications=ineligible_apps,
                top_k_candidates=top_k_candidates,
                candidates_reviewed=candidates_reviewed,
                candidates_advanced=adv_count,
                candidates_rejected=rej_count,
                candidates_held=hold_count,
                offers_extended=offers_ext,
                offers_accepted=offers_acc,
                candidates_hired=cands_hired,
                requisition_fill_status=req_fill_status,
                funnel_conversion=funnel_conv,
                decision_analytics=decision_analytics,
                score_analytics=score_analytics,
                offer_analytics=offer_analytics,
                time_to_first_candidate_days=first_cand_days,
                time_to_first_review_days=first_review_days,
                time_to_first_decision_days=first_decision_days,
                time_to_fill_days=time_to_fill,
                time_to_hire_days=time_to_hire,
            )

    async def get_tenant_aggregated_report(
        self, organization_id: uuid.UUID
    ) -> TenantRequisitionReportResponse:
        async with async_session_factory() as session:
            await session.begin()
            await set_tenant_context(session, organization_id=organization_id)

            stmt_jobs = select(Job).where(Job.organization_id == organization_id)
            jobs = list((await session.execute(stmt_jobs)).scalars().all())

            status_counts = {"DRAFT": 0, "PUBLISHED": 0, "PAUSED": 0, "CLOSED": 0}
            for j in jobs:
                if j.status.value in status_counts:
                    status_counts[j.status.value] += 1

            stmt_apps = select(func.count(Application.id)).where(Application.organization_id == organization_id)
            total_apps = (await session.execute(stmt_apps)).scalar() or 0

            stmt_pl = select(CandidatePlacement).where(
                CandidatePlacement.organization_id == organization_id,
                CandidatePlacement.offer_status == OfferStatusEnum.HIRED,
            )
            hired_placements = list((await session.execute(stmt_pl)).scalars().all())
            total_hired = len(hired_placements)

            ttf_list = []
            tth_list = []
            for p in hired_placements:
                if p.placed_at:
                    job = next((j for j in jobs if j.id == p.job_id), None)
                    if job and job.created_at:
                        ttf_list.append((p.placed_at - job.created_at).total_seconds() / 86400.0)

                    stmt_a = select(Application).where(Application.id == p.application_id)
                    app = (await session.execute(stmt_a)).scalar_one_or_none()
                    if app and app.submitted_at:
                        tth_list.append((p.placed_at - app.submitted_at).total_seconds() / 86400.0)

            avg_ttf = round(float(statistics.mean(ttf_list)), 2) if ttf_list else None
            avg_tth = round(float(statistics.mean(tth_list)), 2) if tth_list else None

            return TenantRequisitionReportResponse(
                organization_id=organization_id,
                total_requisitions=len(jobs),
                requisition_status_counts=status_counts,
                total_applications_all_jobs=total_apps,
                total_hired_all_jobs=total_hired,
                avg_tenant_time_to_fill_days=avg_ttf,
                avg_tenant_time_to_hire_days=avg_tth,
            )

    async def export_requisition_report_csv(
        self, job_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[str]:
        report = await self.get_requisition_report(job_id=job_id, organization_id=organization_id)
        if not report:
            return None

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Metric Category", "Metric Name", "Value"])

        # Overview
        writer.writerow(["Requisition Overview", "Requisition ID", str(report.requisition_id)])
        writer.writerow(["Requisition Overview", "Title", report.title])
        writer.writerow(["Requisition Overview", "Department", report.department or "N/A"])
        writer.writerow(["Requisition Overview", "Location", report.location or "N/A"])
        writer.writerow(["Requisition Overview", "Employment Type", report.employment_type])
        writer.writerow(["Requisition Overview", "Job Status", report.job_status])
        writer.writerow(["Requisition Overview", "Fill Status", report.requisition_fill_status])
        writer.writerow(["Requisition Overview", "Created At", report.created_at.isoformat()])

        # Funnel
        writer.writerow(["Candidate Funnel", "Total Applications", report.total_applications])
        writer.writerow(["Candidate Funnel", "Eligible Applications", report.eligible_applications])
        writer.writerow(["Candidate Funnel", "Ineligible Applications", report.ineligible_applications])
        writer.writerow(["Candidate Funnel", "Top-K Candidates", report.top_k_candidates])
        writer.writerow(["Candidate Funnel", "Candidates Reviewed", report.candidates_reviewed])
        writer.writerow(["Candidate Funnel", "Candidates Advanced", report.candidates_advanced])
        writer.writerow(["Candidate Funnel", "Candidates Rejected", report.candidates_rejected])
        writer.writerow(["Candidate Funnel", "Candidates Held", report.candidates_held])
        writer.writerow(["Candidate Funnel", "Offers Extended", report.offers_extended])
        writer.writerow(["Candidate Funnel", "Offers Accepted", report.offers_accepted])
        writer.writerow(["Candidate Funnel", "Candidates Hired", report.candidates_hired])

        # Funnel Conversion
        writer.writerow(["Funnel Conversion", "Application -> Eligible %", f"{report.funnel_conversion.application_to_eligible_pct}%"])
        writer.writerow(["Funnel Conversion", "Eligible -> Top-K %", f"{report.funnel_conversion.eligible_to_top_k_pct}%"])
        writer.writerow(["Funnel Conversion", "Top-K -> Reviewed %", f"{report.funnel_conversion.top_k_to_reviewed_pct}%"])
        writer.writerow(["Funnel Conversion", "Reviewed -> Advanced %", f"{report.funnel_conversion.reviewed_to_advanced_pct}%"])
        writer.writerow(["Funnel Conversion", "Advanced -> Offer %", f"{report.funnel_conversion.advanced_to_offer_pct}%"])
        writer.writerow(["Funnel Conversion", "Offer -> Accepted %", f"{report.funnel_conversion.offer_to_accepted_pct}%"])
        writer.writerow(["Funnel Conversion", "Accepted -> Hired %", f"{report.funnel_conversion.accepted_to_hired_pct}%"])

        # Score Analytics
        writer.writerow(["Score Analytics", "Average Score", report.score_analytics.average_score if report.score_analytics.average_score is not None else "N/A"])
        writer.writerow(["Score Analytics", "Median Score", report.score_analytics.median_score if report.score_analytics.median_score is not None else "N/A"])
        writer.writerow(["Score Analytics", "Highest Score", report.score_analytics.highest_score if report.score_analytics.highest_score is not None else "N/A"])
        writer.writerow(["Score Analytics", "Lowest Score", report.score_analytics.lowest_score if report.score_analytics.lowest_score is not None else "N/A"])
        writer.writerow(["Score Analytics", "Pass Count", report.score_analytics.pass_count])
        writer.writerow(["Score Analytics", "Fail Count", report.score_analytics.fail_count])

        # Confidence
        writer.writerow(["Confidence Distribution", "HIGH Confidence", report.score_analytics.confidence_distribution.get("HIGH", 0)])
        writer.writerow(["Confidence Distribution", "MEDIUM Confidence", report.score_analytics.confidence_distribution.get("MEDIUM", 0)])
        writer.writerow(["Confidence Distribution", "LOW Confidence", report.score_analytics.confidence_distribution.get("LOW", 0)])

        # Decision Analytics
        writer.writerow(["Decision Analytics", "ADVANCE Count", report.decision_analytics.decision_counts.get("ADVANCE", 0)])
        writer.writerow(["Decision Analytics", "REJECT Count", report.decision_analytics.decision_counts.get("REJECT", 0)])
        writer.writerow(["Decision Analytics", "HOLD Count", report.decision_analytics.decision_counts.get("HOLD", 0)])

        # Time Analytics
        writer.writerow(["Time Analytics", "Time to First Candidate (Days)", report.time_to_first_candidate_days if report.time_to_first_candidate_days is not None else "UNAVAILABLE"])
        writer.writerow(["Time Analytics", "Time to First Review (Days)", report.time_to_first_review_days if report.time_to_first_review_days is not None else "UNAVAILABLE"])
        writer.writerow(["Time Analytics", "Time to First Decision (Days)", report.time_to_first_decision_days if report.time_to_first_decision_days is not None else "UNAVAILABLE"])
        writer.writerow(["Time Analytics", "Time to Fill (Days)", report.time_to_fill_days if report.time_to_fill_days is not None else "UNAVAILABLE"])
        writer.writerow(["Time Analytics", "Time to Hire (Days)", report.time_to_hire_days if report.time_to_hire_days is not None else "UNAVAILABLE"])

        return output.getvalue()
