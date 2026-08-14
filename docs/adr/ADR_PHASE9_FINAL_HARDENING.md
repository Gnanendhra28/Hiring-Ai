# ADR 014: Phase 9 Final Hardening — Gemini Provider & Distributed Worker Architecture

## Context & Problem Statement
Following the Phase 9A–9D architectural audit, two key areas were targeted for pre-Phase 10 remediation:
1. **M-01 Worker Architecture**: Async pipeline execution previously relied on in-process `BackgroundTasks` / `AsyncIO` without an explicit worker abstraction supporting tenant context propagation, correlation IDs, bounded retries, and dead-letter handling.
2. **L-01 Gemini Provider Abstraction**: Google Gemini LLM provider behavior was used in prompt contexts, but `AIGatewayFactory` lacked an explicit `GeminiAIGatewayAdapter`.

## Architectural Decisions Implemented

### 1. Gemini AI Gateway Adapter (`GeminiAIGatewayAdapter`)
- Created [`backend/app/infrastructure/ai_gateway/gemini_adapter.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/infrastructure/ai_gateway/gemini_adapter.py).
- Implements `AIGatewayProvider` with REST API integration for Google Gemini models (`gemini-1.5-flash`).
- Production & Staging Fail-Fast: `GeminiAIGatewayAdapter.__init__()` validates `GEMINI_API_KEY` and raises a `ValueError` if missing or using placeholder secrets in `staging` or `production`.
- `AIGatewayFactory` in [`backend/app/infrastructure/factories.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/infrastructure/factories.py) provides configuration-driven switching between `gemini`, `openai`, and `test`.

### 2. Distributed Event Worker Architecture (`PipelineWorker`)
- Created [`backend/app/infrastructure/workers/pipeline_worker.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/infrastructure/workers/pipeline_worker.py).
- **Tenant Context Propagation**: Invokes `set_tenant_context(session, event.organization_id)` for every transaction to enforce PostgreSQL `FORCE ROW LEVEL SECURITY`.
- **Bounded Retry Handling**: Distinguishes transient failures (retried up to `max_retries = 3`) from permanent failures (e.g. `ValueError` on STALE job intelligence, invalid UUIDs).
- **Dead-Letter Handling**: Routes unresolvable permanent errors or retry-exhausted events to `dead_letter_queue` audit log.
- **Idempotency**: Utilizes database unique constraints (`uq_candidate_job_match_version`, `uq_candidate_job_score_version`, `uq_candidate_job_ranking_version_candidate`, `uq_candidate_recommendation_version_tuple`) to ensure duplicate event processing does not create duplicate scores or recommendations.

### 3. AI Governance & Data Authority Boundaries
- **Recommendation Engine Boundary**: `RecommendationEngine` does NOT calculate scores, ranks, or eligibility. Consumes authoritative Phase 9B scores and Phase 9C ranks.
- **Advisory Recommendations**: Recommendations remain strictly advisory. Recruiter decisions require explicit human user authorization (`decided_by_user_id`). Zero automated application status mutations or email dispatch.

## Verification Summary
- **Backend Quality Gate**: **75 / 75 backend unit and hardening integration tests passing** ($100\%$).
- **Frontend Quality Gate**: TypeScript typecheck, ESLint, and Next.js 14 production build completed with zero errors.
