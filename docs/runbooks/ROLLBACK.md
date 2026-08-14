# Rollback Strategy Runbook

## Overview
Defines non-destructive application and database rollback strategies to preserve authoritative candidate hiring records.

## Application Rollback
If a deployment fails verification, roll back the backend container image to the previous tagged image digest:
```bash
docker pull myregistry/ai-hiring-backend:<previous_stable_tag>
```

## Data Protection Principles
- **No Automatic DB Rollback**: Never run `alembic downgrade` automatically in production.
- **Forward-Only Schema Changes**: All schema additions should be additive (adding columns/tables without dropping existing fields).
- Authoritative hiring data (`CandidateJobScore`, `CandidateJobRanking`, `CandidateDecisionAudit`) remains intact during application rollbacks.
