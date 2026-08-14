# ADR 015: Phase 10 Production Operations, Observability & Scale

## Context & Problem Statement
Operating the AI Hiring Platform at enterprise scale requires production-grade observability, telemetry, API rate limiting, graceful process termination, and worker scalability while strictly preserving AI governance rules (**"AI ASSISTS. RECRUITER DECIDES."**), 100% deterministic candidate scoring/ranking, and PostgreSQL Row Level Security.

## Architectural Decisions Implemented

### 1. High-Performance Metrics & Telemetry Registry (`MetricsRegistry`)
- Created [`backend/app/core/metrics.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/metrics.py).
- Implemented high-performance counters and duration histograms for:
  - `http_requests_total` & `http_request_duration_seconds`
  - `worker_events_received_total`, `worker_events_succeeded_total`, `worker_events_failed_total`, `worker_retries_total`, `worker_dead_letters_total`, `worker_event_duration_seconds`
  - `ai_provider_calls_total`, `ai_tokens_total`, `ai_estimated_cost_usd_total`
- **High-Cardinality Label Guard**: Normalizes request path variables (e.g. `/api/v1/jobs/{id}/recommendations`) and excludes sensitive candidate identifiers (`candidate_id`, `email`, `resume_id`) from metric labels.
- **Prometheus Export**: Mounted `/metrics` endpoint on FastAPI app returning Prometheus-compatible text format.

### 2. Enhanced PII & Secret Log Sanitization (`JSONFormatter`)
- Updated [`backend/app/core/logging.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/logging.py).
- Automatically redacts passwords, tokens, API keys, bearer strings, emails, SSNs, and raw resume texts in structured JSON log entries.
- Injects correlation context (`correlation_id`, `request_id`, `organization_id`, `job_id`, `candidate_id`, `event_id`).

### 3. API Abuse Protection & Rate Limiting (`RateLimiter`)
- Created [`backend/app/core/rate_limiter.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/rate_limiter.py).
- Implements sliding window rate limiting for sensitive endpoints (Auth, Document Uploads, AI Recommendation generation, Heavy Ranking generation).
- Automatically bypassed in `APP_ENV=testing` to ensure fast test execution.
- Returns HTTP 429 Too Many Requests with `Retry-After` response header.

### 4. Resilient Health & Readiness Probes (`/ready` & `/live`)
- Updated `/live` and `/ready` probes in [`backend/app/main.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/main.py).
- **Core System vs AI Provider Readiness**: Distinguishes core database health (PostgreSQL) from optional AI Provider health (Gemini). If Gemini is offline, `/ready` reports `ai_provider: degraded` without returning HTTP 503, ensuring deterministic scoring and ranking APIs remain operational for recruiters.

### 5. Asynchronous Worker Telemetry & Persistent Idempotency (`PipelineWorker`)
- Updated [`backend/app/infrastructure/workers/pipeline_worker.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/infrastructure/workers/pipeline_worker.py).
- Emits real-time worker metrics for event reception, execution duration, bounded retries (max 3), and dead-letter routing.
- Propagates PostgreSQL `FORCE ROW LEVEL SECURITY` context via `set_tenant_context(session, event.organization_id)` for every event transaction.

### 6. Graceful Process Shutdown
- Configured FastAPI `lifespan` context manager in [`backend/app/main.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/main.py) to trap termination signals (`SIGTERM`, `SIGINT`), complete in-flight worker events, and safely dispose of SQLAlchemy database connection pools (`await engine.dispose()`).

## Verification Summary
- **Backend Quality Gate**: **95 / 95 backend tests passing** ($100\%$), 0 `ruff` lint errors.
- **Frontend Quality Gate**: TypeScript typecheck passed, 0 ESLint warnings, Next.js 14 production build completed successfully.
