# Database Backup & Restore Runbook

## Overview
Defines backup policies, retention schedules, and restoration procedures for Azure PostgreSQL with `pgvector` and RLS.

## Backup Policy
- **Automated Daily Backups**: Executed every 24 hours at 00:00 UTC.
- **Point-In-Time Restore (PITR)**: Enabled via PostgreSQL write-ahead logs (WAL) with 30-day retention.
- **Pre-Migration Backups**: Triggered manually prior to executing Alembic DDL schema changes.

## Manual Backup Execution
```bash
pg_dump -h <host> -U <user> -d hiring_db -F c -b -v -f hiring_db_$(date +%Y%m%d_%H%M%S).dump
```

## Manual Restore Execution
```bash
pg_restore -h <host> -U <user> -d hiring_db -v -c hiring_db_<timestamp>.dump
```

## Security & Encryption
- Backup dump files must be encrypted using AES-256 before uploading to cold storage.
- RLS configuration (`FORCE ROW LEVEL SECURITY`) is preserved in `pg_dump` definitions.
