# Cloud Smoke Tests Runbook

## Overview
Defines non-destructive smoke testing sequence for newly deployed Staging and Production environments.

## Non-Destructive Verification Steps
1. **Liveness Probe**: `GET /live` returns HTTP 200 `{"status": "alive"}`.
2. **Readiness Probe**: `GET /ready` returns HTTP 200 `{"status": "ready"}`.
3. **Metrics Endpoint**: `GET /metrics` returns Prometheus text metrics.
4. **Protected Endpoints Security**: `GET /api/v1/jobs` verifies authentication enforcement (`401 Unauthorized` for unauthenticated requests).
5. **Deterministic Pipeline Check**: Verify deterministic scoring (9B) and ranking (9C) endpoints consume zero LLM API tokens.
