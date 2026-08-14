# ADR 013: Candidate Recommendation & Decision Workflow Engine Architecture

## Context & Problem Statement

Phase 9B established the **Deterministic Candidate Scoring Engine** and Phase 9C established the **Deterministic Candidate Ranking & Top-K Selection Engine**. To complete the AI hiring pipeline, Phase 9D provides explainable AI recommendations, strengths, gaps, and evidence citations, and connects deterministic ranking results to a controlled human recruiter decision workflow.

## Decision Drivers & Critical AI Governance Rules

1. **AI ASSISTS. RECRUITER DECIDES.**:
   - AI generates recommendation types (`STRONGLY_RECOMMEND_REVIEW`, `RECOMMEND_REVIEW`, `NEUTRAL_REVIEW`, `REQUIRES_REVIEW`, `NOT_RECOMMENDED_FOR_REVIEW`), recommendation confidence, narrative explanations, strengths, and gaps.
   - AI NEVER automatically hires, rejects, advances, or mutates candidate application status. Consequential workflow transitions require explicit human recruiter authorization.
2. **Authoritative Score & Rank Consumption**: Phase 9D MUST NEVER recompute candidate scores or rankings. Authoritative scores originate strictly from Phase 9B (`overall_score`, `eligibility_status`, `score_confidence`) and rank/Top-K from Phase 9C (`rank_position`, `is_top_k`).
3. **Protected Feature Isolation**: Recommendations strictly exclude protected personal characteristics (gender, race, ethnicity, religion, sexual orientation, disability, health, marital status, age).
4. **Gemini LLM Integration & Graceful Fallback**: Google Gemini AI Gateway provider generates narrative summaries. If Gemini is unavailable, recommendation generation falls back to structured backend reason codes without blocking candidate score or rank access.

## Recommendation Engine Architecture & Decision Audit Trail

### Deterministic Reason Codes & Gemini Explanation
- Backend evaluates deterministic reason codes (`ALL_CRITICAL_REQUIREMENTS_MET`, `STRONG_REQUIRED_SKILL_ALIGNMENT`, `HARD_REQUIREMENT_FAILED`, `TOP_K_CANDIDATE`).
- Gemini turns allowlisted evidence and reason codes into structured recruiter narrative explanations.

### Recruiter Review Workflow & Immutable Decision Audit
- **Review States**: `PENDING_REVIEW`, `UNDER_REVIEW`, `REVIEWED`, `DECISION_REQUIRED`, `DECIDED`.
- **Recruiter Decisions**: `ADVANCE`, `REJECT`, `HOLD`, `REQUEST_MORE_INFORMATION`.
- **Immutable Decision Audit**: Every decision creates an append-only record in `candidate_decision_audits` tracking `organization_id`, `job_id`, `candidate_id`, `application_id`, `decision`, `previous_state`, `new_state`, `decided_by_user_id`, timestamp, and correlation ID. Decision reversals add new audit events.

## Database Security & Row Level Security

- **Database Tables**: `candidate_recommendations`, `candidate_recommendation_reasons`, `candidate_recommendation_evidence`, `candidate_decisions`, `candidate_decision_audits`, `recommendation_processing_audits`.
- **PostgreSQL Row Level Security**: Enabled and forced (`FORCE ROW LEVEL SECURITY`) across all 6 recommendation tables enforcing tenant isolation.

## Status

Accepted and Implemented in Phase 9D.
