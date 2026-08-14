# Staging & Production Go-Live Readiness Checklist

## Overview
This checklist defines the mandatory operational, security, infrastructure, and governance verification gates required before authorizing staging deployment and production traffic cutover.

## 1. Staging Isolation Verification
- [ ] Staging environment isolated in dedicated Resource Group (`rg-staging-eus`).
- [ ] Staging database uses synthetic test data exclusively (zero production PII).
- [ ] Independent Azure Key Vault, Service Bus namespace, and Blob Storage container.

## 2. Infrastructure & Cloud Provisioning
- [ ] Azure Resource Group provisioned.
- [ ] Virtual Network and private subnets (`snet-db`) configured.
- [ ] Azure PostgreSQL Flexible Server 16 provisioned with `pgvector` extension and TLS.
- [ ] Azure Blob Storage container (`documents`) created with private access policy.
- [ ] Azure Service Bus topic (`application-events`) and worker subscription configured.
- [ ] Azure Cache for Redis provisioned for distributed sliding window rate limiting.
- [ ] Azure Key Vault configured with access policy or Workload Identity.

## 3. Secrets & Configuration
- [ ] `DATABASE_URL` stored in Key Vault (no plain text passwords in git or image layers).
- [ ] `SECRET_KEY` and `ENCRYPTION_KEY` set to cryptographically secure strings (min 32 bytes).
- [ ] `GEMINI_API_KEY` stored securely in Key Vault.
- [ ] `CORS_ORIGINS` restricted to verified domains.
- [ ] Application startup validator verifies zero placeholder secrets.

## 4. Database & Migration
- [ ] Pre-deployment database backup executed and verified.
- [ ] `alembic upgrade head` executed cleanly with 0 revision errors.
- [ ] `FORCE ROW LEVEL SECURITY` verified on all 19 database tables across schemas.
- [ ] HNSW vector indexes (`idx_candidate_embeddings_hnsw`, `idx_job_embeddings_hnsw`) active.

## 5. Application & Worker Services
- [ ] Backend API Container App deployed and `/live` returns HTTP 200 `status: alive`.
- [ ] Readiness probe `/ready` evaluates PostgreSQL DB health.
- [ ] Distributed `PipelineWorker` replicas connected to Azure Service Bus.
- [ ] Graceful `SIGTERM`/`SIGINT` process shutdown verified (`await engine.dispose()`).

## 6. Security & AI Governance
- [ ] ScoringEngine (Phase 9B) operates with 100% deterministic logic ($0$ LLM tokens).
- [ ] RankingEngine (Phase 9C) operates with 100% deterministic tie-breaking ($0$ LLM tokens).
- [ ] RecommendationEngine (Phase 9D) outputs advisory recommendations without auto-decisions.
- [ ] Recruiter decisions require explicit human authorization (`decided_by_user_id`).
- [ ] Resume upload path traversal protections and 1MB size limits active.
- [ ] Log sanitizer redacts passwords, tokens, emails, SSNs, and resume text.

## 7. Observability & Telemetry
- [ ] Prometheus metrics exported at `/metrics` with zero candidate PII in label sets.
- [ ] Structured JSON logging with `correlation_id` injection across HTTP and worker flows.
- [ ] Operational alerts configured for 5xx errors, DB pool exhaustion, worker dead-letters, and AI costs.
