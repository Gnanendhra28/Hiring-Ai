# Production Incident & Resiliency Drills

## Overview
Defines simulation procedures and expected platform behavior under operational failure conditions.

## Scenario A: Google Gemini API Unavailable / Outage
- **Simulation**: Temporarily block outbound connection to `generativelanguage.googleapis.com` or pass an invalid model configuration.
- **Expected Platform Behavior**:
  - `/ready` endpoint reports `ai_provider: degraded` while returning HTTP 200 OK.
  - Phase 9B deterministic candidate scoring and Phase 9C candidate ranking continue operating with $0$ disruption.
  - Recommendation engine returns deterministic fallback reason codes without crashing.
  - Recruiter workspace remains responsive.

## Scenario B: Asynchronous Worker Process Failure
- **Simulation**: Terminate all `PipelineWorker` container instances.
- **Expected Platform Behavior**:
  - Domain events accumulate safely in Azure Service Bus queue.
  - Upon worker restart, event processing resumes without data loss.
  - Database unique version constraints (`uq_candidate_job_match_version`, `uq_candidate_job_score_version`, etc.) guarantee idempotency.

## Scenario C: PostgreSQL Database Unavailable
- **Simulation**: Simulate database network isolation.
- **Expected Platform Behavior**:
  - `/ready` endpoint returns HTTP 503 `status: not_ready`.
  - Ingress load balancer stops routing new production traffic to unhealthy instances.

## Scenario D: Distributed Redis Rate Limiter Connection Failure
- **Simulation**: Disconnect Redis cache service.
- **Expected Platform Behavior**:
  - `RedisRateLimiterAdapter` catches connection errors and seamlessly falls back to `InMemoryRateLimiterAdapter`.
  - Endpoint rate limiting remains operational per instance without raising HTTP 500 exceptions.
