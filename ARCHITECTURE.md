# Multi-Tenant AI Hiring SaaS Platform — System Architecture

## 1. Architectural Vision & Scope
This platform is a real, industry-ready, multi-tenant SaaS application designed for end-to-end AI-powered recruitment. It handles up to 300,000+ applications across organizations while maintaining horizontal worker scalability, strict tenant isolation, explainable AI reasoning, and verifiable evidence generation.

---

## 2. High-Level System Architecture

```
                                 [ Client Web Portals ]
                   (Recruiter Portal | Candidate Portal | Admin Portal)
                                           │
                                         HTTPS
                                           ▼
                            [ Azure Front Door / WAF ]
                                           │
                                           ▼
                               [ Next.js Web Frontend ]
                                           │
                                     REST API / JSON
                                           ▼
                               [ FastAPI Backend APIs ]
                                           │
       ┌──────────────────────────────┼──────────────────────────────┐
       ▼                              ▼                              ▼
[ Auth & Multi-Org Engine ] [ Domain Services & Workflows ] [ AI Gateway & Reranker ]
       │                              │                              │
       ▼                              ▼                              ▼
[ PostgreSQL + pgvector (RLS) ] [ Azure Blob Storage ]       [ Azure Service Bus ]
```

---

## 3. Multi-Organization Identity & Tenant Isolation Model

### 3.1 Multi-Organization Identity Model
Users do NOT belong permanently to a single organization. The system enforces a dynamic multi-organization membership model:

```
[ User Identity ]
       │
       ├─► [ Org Membership A ] ──► [ Role & Permissions ] ──► [ Active Org Context A ]
       │
       └─► [ Org Membership B ] ──► [ Role & Permissions ] ──► [ Active Org Context B ]
```

- **Authentication**: Verifies user identity via JWT/OIDC.
- **Organization Membership**: Validates whether the authenticated user has an active membership in the target organization.
- **Active Organization Context**: The frontend passes the requested active organization scope via `X-Organization-ID` header. The backend NEVER blindly trusts this header; authorization middleware verifies that the user possesses valid membership and assigned roles for that specific organization.

### 3.2 Tenant Isolation (Defense in Depth)
Tenant isolation is enforced across 5 defensive layers:

1. **Authentication Layer**: Decodes identity tokens and verifies user identity.
2. **Authorization Middleware**: Validates user membership in the requested active organization context.
3. **Tenant-Aware Service Layer**: Passes `organization_id` explicitly down to domain services.
4. **Tenant-Aware Repository Layer**: Automatically injects `WHERE organization_id = :org_id` into all database queries.
5. **PostgreSQL Row Level Security (RLS)**: Enforces RLS policies at the database engine level.

#### Database Transaction RLS Session Strategy
For every database transaction, the unit-of-work wrapper executes:
```sql
SET LOCAL app.current_organization_id = 'org_uuid_here';
```
PostgreSQL RLS policies evaluate `current_setting('app.current_organization_id', true)` for `SELECT`, `INSERT`, `UPDATE`, and `DELETE` operations, preventing cross-tenant data leaks even in the event of application logic bugs.

---

## 4. Object Storage Isolation & Security

Blob Storage paths follow strict tenant-scoped directory structures:

- **Jobs**: `organizations/{organization_id}/jobs/{job_id}/...`
- **Candidates**: `organizations/{organization_id}/candidates/{candidate_id}/...`
- **Applications**: `organizations/{organization_id}/applications/{application_id}/...`
- **Documents**: `organizations/{organization_id}/documents/{document_id}/{filename}`

The Storage Adapter validates `organization_id` ownership before executing any read, write, or download operation. Path prefixes alone are not treated as the sole security boundary.

---

## 5. Asynchronous Messaging & Service Bus Semantics

- **At-Least-Once Delivery**: Message handling is idempotent. Every event includes `event_id`, `correlation_id`, and `organization_id`.
- **Selective Session Ordering**: Azure Service Bus message sessions are used ONLY where strict sequence ordering is required for a specific aggregate or workflow session (e.g. application state progression). Global FIFO ordering is NOT assumed across all queues.
- **Resilience**: Retries with exponential backoff and Dead-Letter Queues (DLQ) for poison messages.

---

## 6. Observability & Health Probes

### 6.1 Contextual Logging
Logs are formatted in structured JSON and automatically include:
`trace_id`, `span_id`, `correlation_id`, `request_id`, `organization_id`, `user_id`, `event_id`, `job_id`, `application_id`.
Sensitive fields (passwords, tokens, API keys, full resume texts, candidate PII) are strictly redacted by log sanitizers.

### 6.2 Separated Health Probes
- `/live` (Liveness Probe): Returns HTTP 200 OK immediately to verify the process is alive. Performs NO external dependency calls.
- `/ready` (Readiness Probe): Evaluates database (PostgreSQL) and cache (Redis) connectivity according to environment readiness policies. Returns HTTP 200 when ready, or HTTP 503 when degraded.

---

## 7. AI Candidate Retrieval & Feature Matching (Phase 9A)

### 7.1 Strict AI Governance Boundary
Phase 9A is explicitly restricted to **Feature Extraction & Requirement Matching**. It produces structured match evaluations without scoring, ranking, or making automated decisions.

### 7.2 Matching Pipeline
```
[ Versioned Job Intelligence ] ──┐
                                 ├──► [ Matching Service ] ──► [ Feature Match Extractions ]
[ Candidate AI Intelligence ] ──┘          │
                                           ├─► Hard Requirement Engine (GTE, LTE, EQUALS)
                                           ├─► SkillMatcher + SkillNormalizer (Canonical map)
                                           ├─► SemanticMatcher (pgvector cosine similarity)
                                           └─► Protected Feature Filter (Exclusion guard)
```

---

## 8. Deterministic Candidate Scoring Engine (Phase 9B)

### 8.1 Strict AI Governance Boundary
The candidate score is calculated **100% deterministically** from Phase 9A feature evaluations and versioned scoring configurations (`ScoringConfiguration`). No LLM is involved in score calculation.

### 8.2 Hard Requirement Gate & Weight Normalization
- **Hard Requirement Gate**: Any `NOT_MATCHED` hard requirement (`hard_constraint = True`) forces `eligibility_status = FAIL`. High semantic scores cannot override a hard requirement failure.
- **Applicable Weight Normalization**: Non-applicable factor types for a job requisition are dynamically filtered out, and remaining factor weights are normalized to sum to 1.0 ($100\%$).
- **Protected Feature Exclusion**: Requirements flagged `is_protected_feature = True` are strictly excluded from all factor scores and eligibility checks.

---

## 9. Deterministic Candidate Ranking & Top-K Selection Engine (Phase 9C)

### 9.1 Ranking Authority & Zero LLM Principle
Phase 9B is the sole source of truth for candidate scores. Phase 9C consumes authoritative Phase 9B scores (`overall_score`, `eligibility_status`, `score_confidence`) and applies multi-level deterministic tie-breaking. Zero LLM calls occur during ranking.

### 9.2 Ranking & Tie-Breaker Pipeline
```
[ Phase 9B Scores & Eligibility ] ──► [ Eligibility Filtering ]
                                               │
                                               ▼
                                 [ Primary Sort: Score DESC ]
                                               │
                                               ▼
                                 [ Multi-Level Tie-Breakers ]
                                   1. score DESC
                                   2. score_confidence DESC
                                   3. failed_hard_reqs_count ASC
                                   4. matched_reqs_count DESC
                                   5. CandidateJobScore.created_at ASC
                                   6. candidate_id ASC (Deterministic)
                                               │
                                               ▼
                                 [ Rank Position & Top-K Flag ]
```

### 9.3 Top-K Semantics & RLS Security
- Top-K membership (`is_top_k = True`) is assigned AFTER eligibility filtering. Only candidates with `eligibility_status == PASS` and `rank_position <= top_k` receive `is_top_k = True`.
- Versioned ranking snapshots are persisted in `candidate_ranking_versions` and `candidate_job_rankings` with `FORCE ROW LEVEL SECURITY`.

---

## 10. Frontend & Recruiter UX Architecture


### 8.1 Tech Stack & UI Principles
- **Stack**: Next.js 14.2.x (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod.
- **Design Standard**: Premium, clean, responsive, accessible, enterprise-grade.
- **Selective 3D**: Three.js / React Three Fiber is reserved strictly for high-value visual models.
- **No Fake Data Policy**: Production UI displays real backend data, proper loading/skeleton states during async operations, empty states when no data exists, and real error banners on failures.

### 8.2 Recruiter Job Workspace
The **Job Workspace** is the central recruiter hub containing sub-views:
1. **Overview**: Key metrics, hiring progress, action items.
2. **Applications**: Complete applicant table with filterable pipeline states.
3. **AI Ranking**: Explainable ranking view (Overall Match, Confidence, Score Breakdown, Strengths, Gaps, Evidence, Uncertainty, AI Recommendation).
4. **Shortlisted**: Candidates approved for evaluation.
5. **Assessments**: Test status & scoring.
6. **Interviews**: Calendar slot management & interviewer feedback.
7. **Offers**: Offer generation & status tracking.
8. **Communications**: Draft email reviews & delivery logs.
9. **Analytics**: Funnel performance & time-to-hire.

---

## 9. AI Safety & Decision Governance

AI recommendations NEVER execute irreversible hiring actions automatically.
```
AI Engine ──► Recommendation ──► Confidence & Evidence ──► Workflow Gate ──► Human Approval ──► State Transition
```
Human recruiter or admin approval is MANDATORY for shortlisting, sending rejections, issuing assessment/interview invitations, sending offers, or executing consequential candidate communications.

---

## 11. Candidate Recommendation & Recruiter Decision Workflow Engine (Phase 9D)

### 11.1 Critical AI Governance Rule
**AI ASSISTS. RECRUITER DECIDES.**
The AI model generates recommendation classifications (`STRONGLY_RECOMMEND_REVIEW`, `RECOMMEND_REVIEW`, `NEUTRAL_REVIEW`, `REQUIRES_REVIEW`, `NOT_RECOMMENDED_FOR_REVIEW`), recommendation confidence, narrative summaries, strengths, gaps, and evidence quotes. The AI NEVER makes automated hiring decisions or application status mutations. Consequential state transitions require explicit human recruiter authorization.

### 11.2 Architectural Flow & Authoritative Score Integrity
```
[ Phase 9B Authoritative Score ] ──┐
                                   ├──► [ Recommendation Engine ] ──► [ AI Explanations & Reasons ]
[ Phase 9C Authoritative Rank ]  ──┘           │
                                               ├─► Google Gemini Provider Adapter (Allowlist Context)
                                               ├─► Protected Feature Isolation (Excludes PII/age/gender)
                                               ├─► Grounded Evidence Citations (Resume Text & Page)
                                               └─► Recruiter Decision Hub (Human Authorization Required)
```
- **Zero Score/Rank Recomputation**: Phase 9D MUST NEVER recompute candidate scores or rankings.
- **Immutable Decision Audit**: Recruiter decisions (`ADVANCE`, `REJECT`, `HOLD`, `REQUEST_MORE_INFORMATION`) log append-only records to `candidate_decision_audits` with `organization_id`, `job_id`, `candidate_id`, `application_id`, `decision`, `decided_by_user_id`, timestamp, and correlation ID.
- **PostgreSQL Row Level Security**: `candidate_recommendations`, `candidate_recommendation_reasons`, `candidate_recommendation_evidence`, `candidate_decisions`, `candidate_decision_audits`, and `recommendation_processing_audits` enforce tenant isolation via `FORCE ROW LEVEL SECURITY`.

---

## 12. Phase 9 Final Hardening — Gemini Provider & Distributed Worker Architecture

### 12.1 Google Gemini AI Gateway Provider (`GeminiAIGatewayAdapter`)
- **Adapter**: Implements `AIGatewayProvider` with REST API integration for Google Gemini models (`gemini-1.5-flash`).
- **Fail-Fast Credential Validation**: In `staging` or `production` environments, `GeminiAIGatewayAdapter` validates `GEMINI_API_KEY` and raises a `ValueError` if credentials are missing or placeholder keys.
- **Provider Selection**: `AIGatewayFactory` provides configuration-driven provider selection (`gemini`, `openai`, `test`).

### 12.2 Distributed Event Worker Architecture (`PipelineWorker`)
- **Asynchronous Pipeline Processing**: Async worker processing isolates event handling from HTTP request paths.
- **Tenant Context Propagation**: Invokes `set_tenant_context(session, event.organization_id)` for every transaction to enforce PostgreSQL `FORCE ROW LEVEL SECURITY`.
- **Bounded Retries & Dead-Letter Handling**: Distinguishes transient failures (retried up to `max_retries = 3`) from permanent failures (e.g., STALE job intelligence, invalid UUIDs). Unresolvable errors are routed to the `dead_letter_queue` audit log.
- **Database Idempotency**: Utilizes DB unique constraints to ensure duplicate delivery of events produces zero duplicate scores or recommendations.

---

## 13. Phase 10 Production Operations, Observability & Enterprise Scale

### 13.1 Operational Telemetry & Prometheus Metrics
- **Registry**: High-performance `MetricsRegistry` in [`backend/app/core/metrics.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/metrics.py) exporting Prometheus format at `/metrics`.
- **Metrics Tracked**: HTTP request counts/latencies, worker event processing/retries/dead-letters, AI provider calls/token usage/costs.
- **Label Hygiene**: Omits sensitive candidate identifiers (`candidate_id`, `email`, `resume_id`) from metric labels.

### 13.2 API Abuse Protection & Rate Limiting
- **RateLimiter**: Sliding window rate limiter in [`backend/app/core/rate_limiter.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/rate_limiter.py) enforcing per-IP rate limits on sensitive endpoints.
- **Test Environment Bypass**: Bypassed automatically when `APP_ENV=testing`.

### 13.3 Health & Readiness Strategy
- `/live`: Immediate process liveness.
- `/ready`: Verifies database connection. Reports AI Provider status as `degraded` if offline without returning HTTP 503 so deterministic scoring/ranking remain functional.

---

## 15. Phase 12 Production Cloud Infrastructure Architecture

### 15.1 Provider-Isolated Cloud Adapters
- **Event Bus**: `AzureServiceBusEventBus` implements `EventBus` for production pub/sub topic handling.
- **Distributed Rate Limiting**: `RedisRateLimiterAdapter` implements `IRateLimiterProvider` with automatic fallback to `InMemoryRateLimiterAdapter`.
- **Secret Management**: `SecretProvider` in [`backend/app/core/secrets.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/secrets.py) provides environment and Azure Key Vault secret retrieval.

### 15.2 Infrastructure as Code (`infra/terraform/`)
- Modular Terraform configuration (`main.tf`, `variables.tf`, `outputs.tf`) provisioning Azure Resource Group, Virtual Network & Private Subnets, Azure Container Registry (ACR), Azure Container Apps, Azure PostgreSQL Flexible Server with `pgvector` & RLS, Azure Blob Storage, Azure Service Bus, and Azure Key Vault.

### 15.3 CI/CD Deployment Pipeline (`.github/workflows/deploy.yml`)
- Multi-stage pipeline: `Lint & Tests` -> `Container Build` -> `Staging Deployment` -> `Production Manual Approval Gate` -> `Production Deployment`.

---

## 16. Phase 13 Production Cloud Deployment, Go-Live & Operational Validation

### 16.1 Environment Credential Verification & Deployment Status
- **Authentication Check**: Inspected execution environment for Azure CLI login and subscription credentials.
- **Deployment Status**: Production cloud deployment artifacts, Terraform specifications, runbooks, and quality gates are $100\%$ validated locally. Pursuant to governance rules, actual Azure cloud provisioning was not executed due to missing active cloud subscription credentials.

### 16.2 Go-Live & Incident Drill Framework
- **Operational Runbooks**: Documented in `docs/runbooks/` (`GO_LIVE_CHECKLIST.md`, `PRODUCTION_VALIDATION.md`, `PRODUCTION_INCIDENT_DRILLS.md`).
- **Resiliency Guarantees**: Under simulated Google Gemini API outages, `/ready` reports `ai_provider: degraded` while system traffic remains alive (HTTP 200 OK). Deterministic scoring (Phase 9B) and ranking (Phase 9C) operate with zero disruption.

---

## 17. Runtime Technology Summary

| Component | Specification |
|---|---|
| Runtime | Python 3.13 |
| Backend Framework | FastAPI 0.110+ |
| Database | Azure PostgreSQL (with `pgvector`) + RLS |
| Cache | Redis 7 / Azure Cache for Redis |
| Storage | Azure Blob Storage |
| Messaging | Azure Service Bus / Distributed Event Bus |
| AI Gateway | Google Gemini 1.5 Flash / OpenAI / Test Adapter |
| Secret Storage | Azure Key Vault / Environment Variables |
| Infrastructure | Terraform (Azure IaC) |
| Telemetry | Prometheus Metrics + JSON Structured Logging |
| Frontend | Next.js 14.2.x + React 18 + TypeScript + Tailwind CSS |
| Observability | OpenTelemetry + Azure Monitor |





