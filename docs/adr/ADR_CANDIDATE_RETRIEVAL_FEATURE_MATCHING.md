# ADR: Candidate Retrieval & Feature Matching Engine (Phase 9A)

## Status
ACCEPTED

## Context
Phase 9A introduces candidate document retrieval and feature matching against versioned Job Intelligence (Phase 8).
Per AI Governance rules, Phase 9A is strictly a **Feature Extraction & Matching Layer**. It MUST NOT calculate candidate match scores, rankings, Top-K lists, or make automated hiring decisions.

## Architecture & Decisions

### 1. Dual-Version Tracking & Stale Guard
- Every candidate matching record strictly stores both `job_intelligence_version_id` and `candidate_document_id`.
- If the active `JobIntelligenceVersion` is flagged as `STALE`, candidate feature matching fails-fast and blocks execution until Job Intelligence is regenerated.

### 2. Normalized Relational Match Tables with RLS
- Five tables created with `FORCE ROW LEVEL SECURITY`:
  - `candidate_job_matches`: Overall matching status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `OUTDATED`) and audit fields.
  - `candidate_requirement_matches`: Evaluates individual job requirements against candidate profiles (`MATCHED`, `PARTIALLY_MATCHED`, `NOT_MATCHED`, `UNKNOWN`, `NOT_APPLICABLE`, `PROTECTED_EXCLUDED`). Absence of evidence explicitly returns `UNKNOWN` instead of `NOT_MATCHED`.
  - `candidate_semantic_matches`: Cosine similarity across 3 pgvector context pairs (`REQUIRED_SKILLS` $\leftrightarrow$ `SKILL_CONTEXT`, `RESPONSIBILITIES` $\leftrightarrow$ `EXPERIENCE_CONTEXT`, `JOB_INTENT` $\leftrightarrow$ `SUMMARY`).
  - `match_evidence`: Exact/normalized quotes verified via `EvidenceVerifier` from candidate document text.
  - `match_processing_audits`: Audit logging for processing duration and version metadata.

### 3. Hard Requirement & Protected Feature Evaluation
- `HardRequirementEngine`: Evaluates experience constraints (`GTE`, `LTE`, `EQUALS`, `RANGE`) in normalized `MONTHS` and work mode compatibility without using float scoring.
- `SkillMatcher` & `SkillNormalizer`: Reuses Phase 7 canonical skill mapping (`RAG` $\rightarrow$ `RAG`) and `EvidenceVerifier`. Hallucinated evidence quotes receive a confidence penalty.
- `ProtectedFeatureFilter`: Requirements marked `is_protected_feature = True` automatically receive status `PROTECTED_EXCLUDED` and are blocked from contributing to candidate feature evaluations.

### 4. Recruiter Transparency UI
- Recruiter evidence view presents granular requirement match statuses (`✓ MATCHED`, `? UNKNOWN`, `× NOT MATCHED`), pgvector context similarities, and exact verified quotes.
- Displays **zero overall scores or candidate ranks**.

## Consequences
- Future Phase 9B scoring engine will consume structured feature evaluations produced by Phase 9A without needing to rerun raw document parsing or vector searches.
