# Production Deployment Runbook

## Overview
This runbook defines the step-by-step production deployment sequence for the AI Hiring Platform.

## Pre-Deployment Checklist
1. All CI quality gates (`backend` unit tests, `ruff`, `frontend` typecheck, ESLint, Next.js build) must pass on `main`.
2. Secure secrets (`SECRET_KEY`, `ENCRYPTION_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`) must be loaded into production environment variables or Azure Key Vault.
3. Database backup must be executed prior to running migrations.

## Deployment Sequence
```
[ Database Backup ] ──► [ Alembic Migrations ] ──► [ FastAPI App Update ] ──► [ Pipeline Workers ] ──► [ Frontend Update ]
```

1. **Database Migration**:
   ```bash
   cd backend
   alembic upgrade head
   ```
2. **Backend Application**:
   Deploy updated Docker container. Verify `/live` returns HTTP 200 and `/ready` reports `ready`.
3. **Pipeline Worker**:
   Deploy worker instance. Verify worker connects to DB and processes domain events.
4. **Frontend**:
   Deploy Next.js production build (`npm run build`).

## Post-Deployment Verification
- Test `/live` and `/ready` health endpoints.
- Test `/metrics` endpoint to ensure Prometheus scrapers receive telemetry.
