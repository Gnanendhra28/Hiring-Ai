# Disaster Recovery Runbook

## Service Level Objectives
- **Recovery Point Objective (RPO)**: < 1 Hour (maximum acceptable data loss window).
- **Recovery Time Objective (RTO)**: < 4 Hours (maximum acceptable downtime duration).

## Disaster Scenarios & Recovery Workflows

### 1. Database Outage / Regional Failure
1. Trigger Azure PostgreSQL geo-redundant failover to secondary region.
2. Verify connection string in environment variables (`DATABASE_URL`).
3. Run `/ready` health probe to confirm DB readiness.

### 2. External AI Gateway Outage (Google Gemini Failure)
- Deterministic candidate scoring (Phase 9B) and deterministic candidate ranking (Phase 9C) operate with **0 LLM calls**.
- AI recommendation generation (Phase 9D) automatically falls back to deterministic reason codes.
- `/ready` endpoint reports `ai_provider: degraded` while keeping platform traffic alive (HTTP 200 OK).

### 3. Worker Process Failure
1. Unprocessed pipeline events remain in dead-letter or event queue logs.
2. Restart `PipelineWorker` processes.
3. Database unique constraints (`uq_candidate_job_match_version`, `uq_candidate_job_score_version`, etc.) ensure zero duplicate records on event replay.
