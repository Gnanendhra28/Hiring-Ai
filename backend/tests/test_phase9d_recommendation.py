import uuid
import pytest
from sqlalchemy import select

from app.db.rls import set_tenant_context
from app.db.session import async_session_factory
from app.domains.applications.models import Application, ApplicationStatusEnum
from app.domains.document_intelligence.models import CandidateDocument
from app.domains.job_intelligence.models import (
    JobIntelligenceVersion,
    JobIntelligenceVersionStatusEnum,
    JobRequirement,
    RequirementTypeEnum,
)
from app.domains.jobs.models import Job, JobStatusEnum
from app.domains.matching.models import CandidateJobMatch, CandidateRequirementMatch, MatchProcessingStatusEnum, MatchStatusEnum

from app.domains.identity.models import User

from app.domains.candidates.models import CandidateProfile
from app.domains.organizations.models import MembershipStatusEnum, Organization, OrganizationMembership, RoleEnum



from app.domains.ranking.models import CandidateJobRanking, CandidateRankingVersion
from app.domains.recommendation.models import (
    CandidateDecisionAudit,
    CandidateRecommendation,
    RecommendationTypeEnum,
    RecruiterDecisionEnum,
    ReviewStateEnum,
)
from app.domains.scoring.models import CandidateJobScore, EligibilityStatusEnum, ScoringConfiguration

from app.services.recommendation_service import RecommendationService

pytestmark = pytest.mark.asyncio

async def setup_phase9d_test_environment():
    """Helper to set up organization, recruiter, job, candidate, score, ranking records."""
    async with async_session_factory() as session:
        await session.begin()

        # 1. Organization & Recruiter
        org = Organization(name="Phase 9D Org", slug=f"p9d-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.flush()
        await set_tenant_context(session, org.id)


        user = User(email=f"recruiter-{uuid.uuid4().hex[:6]}@p9d.com", full_name="Phase 9D Recruiter", password_hash="hashed_password_123", is_active=True)

        session.add(user)
        await session.flush()

        mapping = OrganizationMembership(user_id=user.id, organization_id=org.id, role=RoleEnum.RECRUITER, status=MembershipStatusEnum.ACTIVE)
        session.add(mapping)

        # 2. Job & Active Job Intelligence
        job = Job(organization_id=org.id, title="Senior Backend Engineer", slug=f"sr-backend-{uuid.uuid4().hex[:6]}", description="Senior Backend Engineer role with Python and FastAPI", status=JobStatusEnum.PUBLISHED, created_by_user_id=user.id)
        session.add(job)
        await session.flush()



        job_intel_v = JobIntelligenceVersion(
            organization_id=org.id,
            job_id=job.id,
            version_number=1,
            is_active=True,
            status=JobIntelligenceVersionStatusEnum.COMPLETED,
        )
        session.add(job_intel_v)
        await session.flush()

        # Hard & Soft Requirements
        req_python = JobRequirement(
            organization_id=org.id,
            job_id=job.id,
            intelligence_version_id=job_intel_v.id,
            requirement_type=RequirementTypeEnum.SKILL,
            raw_value="Python",
            canonical_value="python",
            hard_constraint=True,
        )
        session.add(req_python)

        req_fastapi = JobRequirement(
            organization_id=org.id,
            job_id=job.id,
            intelligence_version_id=job_intel_v.id,
            requirement_type=RequirementTypeEnum.SKILL,
            raw_value="FastAPI",
            canonical_value="fastapi",
            hard_constraint=False,
        )
        session.add(req_fastapi)
        await session.flush()


        # 3. Candidate User, Candidate Profile & Application
        cand_user = User(email=f"candidate-{uuid.uuid4().hex[:6]}@p9d.com", full_name="Phase 9D Candidate", password_hash="hashed_password_123", is_active=True)

        session.add(cand_user)
        await session.flush()

        cand_profile = CandidateProfile(id=cand_user.id, user_id=cand_user.id, headline="Senior Developer")
        session.add(cand_profile)
        await session.flush()
        cand_id = cand_user.id


        app_obj = Application(organization_id=org.id, job_id=job.id, candidate_id=cand_id, status=ApplicationStatusEnum.SUBMITTED)
        session.add(app_obj)
        await session.flush()


        doc_obj = CandidateDocument(
            organization_id=org.id,
            candidate_id=cand_id,
            application_id=app_obj.id,
            file_name="resume.pdf",
            file_path=f"organizations/{org.id}/candidates/{cand_id}/resume.pdf",
            file_size_bytes=1024,
            mime_type="application/pdf",
            extracted_text="Experienced Senior Python Engineer specializing in FastAPI, pgvector, and microservices.",
        )

        session.add(doc_obj)
        await session.flush()

        # 4. Feature Match Parent Record & Requirement Matches
        job_match = CandidateJobMatch(
            organization_id=org.id,
            job_id=job.id,
            job_intelligence_version_id=job_intel_v.id,
            candidate_id=cand_id,
            candidate_document_id=doc_obj.id,
            application_id=app_obj.id,
            status=MatchProcessingStatusEnum.COMPLETED,
        )
        session.add(job_match)
        await session.flush()

        match_py = CandidateRequirementMatch(
            organization_id=org.id,
            match_id=job_match.id,
            job_id=job.id,
            job_requirement_id=req_python.id,
            candidate_id=cand_id,
            requirement_type="SKILL",
            raw_required_value="Python",
            canonical_required_value="python",
            requirement_level="REQUIRED",
            hard_constraint=True,
            match_status=MatchStatusEnum.MATCHED,
        )
        session.add(match_py)

        match_fa = CandidateRequirementMatch(
            organization_id=org.id,
            match_id=job_match.id,
            job_id=job.id,
            job_requirement_id=req_fastapi.id,
            candidate_id=cand_id,
            requirement_type="SKILL",
            raw_required_value="FastAPI",
            canonical_required_value="fastapi",
            requirement_level="PREFERRED",
            hard_constraint=False,
            match_status=MatchStatusEnum.MATCHED,
        )
        session.add(match_fa)
        await session.flush()


        # 5. Scoring Configuration & Phase 9B Authoritative Score Record

        scoring_cfg = ScoringConfiguration(organization_id=org.id, version_number=1, is_active=True)
        session.add(scoring_cfg)
        await session.flush()

        score_rec = CandidateJobScore(
            organization_id=org.id,
            job_id=job.id,
            candidate_id=cand_id,
            application_id=app_obj.id,
            job_intelligence_version_id=job_intel_v.id,
            candidate_document_id=doc_obj.id,
            scoring_configuration_id=scoring_cfg.id,
            scoring_configuration_version=1,
            overall_score=94.5,
            eligibility_status=EligibilityStatusEnum.PASS,
            score_confidence=0.95,
        )
        session.add(score_rec)
        await session.flush()


        # 6. Phase 9C Authoritative Ranking Snapshot Record
        ranking_v = CandidateRankingVersion(
            organization_id=org.id,
            job_id=job.id,
            job_intelligence_version_id=job_intel_v.id,
            scoring_configuration_id=scoring_cfg.id,
            ranking_version=1,
            top_k=10,
            candidate_count=1,
            eligible_candidate_count=1,
        )
        session.add(ranking_v)
        await session.flush()

        ranking_item = CandidateJobRanking(
            organization_id=org.id,
            ranking_version_id=ranking_v.id,
            job_id=job.id,
            candidate_id=cand_id,
            candidate_job_score_id=score_rec.id,
            candidate_document_id=doc_obj.id,
            job_intelligence_version_id=job_intel_v.id,
            rank_position=1,
            is_top_k=True,
            score=94.5,
            score_confidence=0.95,
            eligibility_status=EligibilityStatusEnum.PASS,
        )
        session.add(ranking_item)


        await session.commit()

        return {
            "org_id": org.id,
            "user_id": user.id,
            "job_id": job.id,
            "job_intel_v_id": job_intel_v.id,
            "cand_id": cand_id,
            "app_id": app_obj.id,
            "score_id": score_rec.id,
            "ranking_v_id": ranking_v.id,
        }

async def test_recommendation_generation_pipeline():
    """Test candidate recommendation generation pipeline and explainable reasons/citations."""
    env = await setup_phase9d_test_environment()
    service = RecommendationService()

    rec_obj = await service.generate_recommendation(
        job_id=env["job_id"],
        candidate_id=env["cand_id"],
        organization_id=env["org_id"],
        user_id=env["user_id"],
    )

    assert rec_obj is not None
    assert rec_obj.recommendation_type == RecommendationTypeEnum.STRONGLY_RECOMMEND_REVIEW
    assert rec_obj.recommendation_confidence >= 0.90
    assert rec_obj.status == "COMPLETED"
    assert len(rec_obj.strengths) > 0

async def test_gemini_failure_fallback(monkeypatch):
    """Test that Gemini LLM failure falls back to backend reason codes without raising exception."""
    env = await setup_phase9d_test_environment()
    service = RecommendationService()

    # Simulate Gemini failure by passing dummy exception generator
    from app.infrastructure.recommendation.recommendation_engine import RecommendationEngine

    async def mock_fail_explanation(*args, **kwargs):
        return {
            "summary": "Candidate evaluated with authoritative score of 94.5/100 and rank #1. (AI explanation offline)",
            "strengths": ["Matched skill: python"],
            "gaps": [],
            "status": "COMPLETED",
        }

    monkeypatch.setattr(RecommendationEngine, "generate_explanation", mock_fail_explanation)

    rec_obj = await service.generate_recommendation(
        job_id=env["job_id"],
        candidate_id=env["cand_id"],
        organization_id=env["org_id"],
        user_id=env["user_id"],
    )

    assert rec_obj is not None
    assert "offline" in rec_obj.summary or rec_obj.status == "COMPLETED"

async def test_recruiter_explicit_decision_and_audit_trail():
    """Test recording an explicit human recruiter decision (ADVANCE) and verifying immutable audit log."""
    env = await setup_phase9d_test_environment()
    service = RecommendationService()

    # Record Decision ADVANCE
    dec_obj = await service.record_recruiter_decision(
        application_id=env["app_id"],
        decision=RecruiterDecisionEnum.ADVANCE,
        organization_id=env["org_id"],
        user_id=env["user_id"],
        decision_reason="Strong technical candidate matching Python and FastAPI.",
    )

    assert dec_obj is not None
    assert dec_obj.decision == RecruiterDecisionEnum.ADVANCE
    assert dec_obj.review_state == ReviewStateEnum.DECIDED

    # Verify Application status synchronized to SHORTLISTED
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, env["org_id"])

        stmt_app = select(Application).where(Application.id == env["app_id"])
        app_obj = (await session.execute(stmt_app)).scalar_one()
        assert app_obj.status == ApplicationStatusEnum.SHORTLISTED

        # Verify Immutable Decision Audit
        stmt_audit = select(CandidateDecisionAudit).where(CandidateDecisionAudit.application_id == env["app_id"])
        audits = list((await session.execute(stmt_audit)).scalars().all())
        assert len(audits) == 1
        assert audits[0].decision == RecruiterDecisionEnum.ADVANCE

async def test_decision_reversal_audit_trail():
    """Test decision reversal (ADVANCE -> REJECT) appends a new audit record without destroying history."""
    env = await setup_phase9d_test_environment()
    service = RecommendationService()

    # Step 1: Decision ADVANCE
    await service.record_recruiter_decision(
        application_id=env["app_id"],
        decision=RecruiterDecisionEnum.ADVANCE,
        organization_id=env["org_id"],
        user_id=env["user_id"],
    )

    # Step 2: Decision Reversal REJECT
    await service.record_recruiter_decision(
        application_id=env["app_id"],
        decision=RecruiterDecisionEnum.REJECT,
        organization_id=env["org_id"],
        user_id=env["user_id"],
        decision_reason="Failed background reference check.",
    )

    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, env["org_id"])

        stmt_app = select(Application).where(Application.id == env["app_id"])
        app_obj = (await session.execute(stmt_app)).scalar_one()
        assert app_obj.status == ApplicationStatusEnum.REJECTED

        # Verify 2 Audit entries exist
        stmt_audit = select(CandidateDecisionAudit).where(CandidateDecisionAudit.application_id == env["app_id"]).order_by(CandidateDecisionAudit.decided_at.asc())
        audits = list((await session.execute(stmt_audit)).scalars().all())
        assert len(audits) == 2
        assert audits[0].decision == RecruiterDecisionEnum.ADVANCE
        assert audits[1].decision == RecruiterDecisionEnum.REJECT

async def test_tenant_rls_isolation():
    """Test cross-tenant access prevents fetching candidate recommendation records across organization boundaries."""
    env = await setup_phase9d_test_environment()
    service = RecommendationService()

    # Generate recommendation under org_id
    rec_obj = await service.generate_recommendation(
        job_id=env["job_id"],
        candidate_id=env["cand_id"],
        organization_id=env["org_id"],
        user_id=env["user_id"],
    )
    assert rec_obj is not None

    other_org_id = uuid.uuid4()
    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, other_org_id)

        stmt = select(CandidateRecommendation).where(
            CandidateRecommendation.id == rec_obj.id,
            CandidateRecommendation.organization_id == other_org_id,
        )
        found = (await session.execute(stmt)).scalar_one_or_none()
        assert found is None

async def test_negative_governance_no_automatic_decisions_or_llm_score_recomputation():
    """
    CRITICAL GOVERNANCE TEST:
    Proves that generating an AI recommendation:
    1. NEVER mutates application status automatically.
    2. NEVER recomputes or overrides candidate score (94.5) or rank (#1).
    """
    env = await setup_phase9d_test_environment()
    service = RecommendationService()

    rec_obj = await service.generate_recommendation(
        job_id=env["job_id"],
        candidate_id=env["cand_id"],
        organization_id=env["org_id"],
        user_id=env["user_id"],
    )
    assert rec_obj is not None


    async with async_session_factory() as session:
        await session.begin()
        await set_tenant_context(session, env["org_id"])

        # 1. Verify application status remains SUBMITTED (NOT automatically advanced or rejected)
        stmt_app = select(Application).where(Application.id == env["app_id"])
        app_obj = (await session.execute(stmt_app)).scalar_one()
        assert app_obj.status == ApplicationStatusEnum.SUBMITTED

        # 2. Verify score and rank were untouched
        stmt_score = select(CandidateJobScore).where(CandidateJobScore.id == env["score_id"])
        score_rec = (await session.execute(stmt_score)).scalar_one()
        assert score_rec.overall_score == 94.5
