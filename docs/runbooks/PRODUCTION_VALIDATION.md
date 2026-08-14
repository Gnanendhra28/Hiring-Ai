# Production Operational Validation Runbook

## Overview
This runbook provides step-by-step procedures for validating a live production or staging deployment.

## 1. System Health Probes
```bash
# Liveness Check
curl -f -s https://api.hiringplatform.com/live

# Readiness Check
curl -f -s https://api.hiringplatform.com/ready

# Prometheus Telemetry Export
curl -f -s https://api.hiringplatform.com/metrics
```

## 2. Tenant RLS Isolation Verification
Execute a synthetic tenant isolation verification using test organization IDs:
```sql
-- Transaction A: Org A context
SET LOCAL app.current_organization_id = '11111111-1111-1111-1111-111111111111';
SELECT COUNT(*) FROM candidate_job_scores;

-- Transaction B: Org B context
SET LOCAL app.current_organization_id = '22222222-2222-2222-2222-222222222222';
SELECT COUNT(*) FROM candidate_job_scores;
```
Verify Transaction A returns zero rows belonging to Org B, confirming PostgreSQL `FORCE ROW LEVEL SECURITY`.

## 3. AI Governance & Data Authority Validation
1. Verify `ScoringEngine` and `RankingEngine` generate outputs without making HTTP requests to Google Gemini.
2. Verify candidate recommendations populate advisory narratives (`STRONGLY_RECOMMEND_REVIEW`, `RECOMMEND_REVIEW`) without modifying `Application.status`.
3. Verify recruiter decision endpoints (`/api/v1/jobs/{job_id}/candidates/{candidate_id}/decisions`) write immutable records to `candidate_decision_audits`.
