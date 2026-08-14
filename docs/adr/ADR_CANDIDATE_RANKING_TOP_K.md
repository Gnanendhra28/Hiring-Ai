# ADR 012: Candidate Ranking & Top-K Selection Engine Architecture

## Context & Problem Statement

Phase 9B established the **Deterministic Candidate Scoring Engine**, producing authoritative candidate factor scores, overall scores ($0-100$), and eligibility statuses (`PASS`/`FAIL`). To support recruiter decision workflows, the platform requires a deterministic candidate ranking and Top-K selection mechanism.

## Decision Drivers & Critical AI Governance Rules

1. **Zero LLM Calls in Ranking**: Ranking MUST be 100% deterministic based on authoritative Phase 9B candidate scores and explicit multi-level tie-breaking rules. No LLM is permitted to assign ranks or order candidates.
2. **Authoritative Score Consumption**: Phase 9B is the sole source of truth for candidate scores (`overall_score`, `eligibility_status`, `score_confidence`). Phase 9C does NOT alter scores or compute new formulas.
3. **Eligibility-Aware Ranking & Top-K**: Candidates with `eligibility_status == FAIL` are ranked below all eligible candidates and can NEVER consume a Top-K slot (`is_top_k = False`).
4. **Zero Automatic Workflow Actions**: Ranking is decision-support data only. No automatic shortlist, rejection, or application status mutations occur.

## Deterministic Ranking & Multi-Level Tie-Breaking Rules

Given identical candidate scores, candidate document versions, and job intelligence versions, ranking generation is strictly reproducible.

### Primary Ordering
1. `eligibility_status == PASS` ahead of `FAIL` (eligible candidates outrank ineligible candidates)
2. `overall_score DESC`

### Multi-Level Tie-Breaker Ordering
When two or more candidates possess identical `overall_score`:
1. `overall_score DESC`
2. `score_confidence DESC`
3. `failed_hard_reqs_count ASC` (fewer hard failures ranks higher)
4. `matched_reqs_count DESC` (more matched requirement features ranks higher)
5. `CandidateJobScore.created_at ASC` (earlier score calculation ranks higher)
6. `candidate_id ASC` (string representation alphabetical order guarantees strictly deterministic ordering)

## Top-K Selection Semantics

- Top-K membership is assigned AFTER eligibility filtering.
- Only candidates with `eligibility_status == PASS` and `rank_position <= top_k` receive `is_top_k = True`.
- Ineligible candidates (`eligibility_status == FAIL`) can NEVER consume a Top-K slot.

## Versioning & Database Security

- **Database Tables**:
  - `candidate_ranking_versions`: Versioned ranking snapshot metadata (`ranking_version`, `top_k`, `candidate_count`, `eligible_candidate_count`, `ineligible_candidate_count`).
  - `candidate_job_rankings`: Normalized candidate ranking result table (`rank_position`, `is_top_k`, `eligibility_status`, `score`, `score_confidence`). Unique index `uq_candidate_job_ranking_version_candidate`.
  - `ranking_processing_audits`: Processing duration and correlation audit trail.
- **PostgreSQL Row Level Security**: Enabled and forced (`FORCE ROW LEVEL SECURITY`) across all 3 ranking tables enforcing tenant isolation.

## Status

Accepted and Implemented in Phase 9C.
