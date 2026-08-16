# Production Operational Handover & System Continuity Runbook

## 1. Overview & Scope

This runbook defines operational handover procedures, deployment validation gates, container restart workflows, incident severity levels, and 20 recovery scenarios for the AI Hiring SaaS Platform.

> [!IMPORTANT]
> **GOVERNANCE PRINCIPLE**: "AI ASSISTS. RECRUITER DECIDES." Deployment operations and maintenance MUST NOT modify recruiter decision records or introduce autonomous hiring mutations.

> [!NOTE]
> **DEPLOYMENT STRATEGY NOTICE**: In the current single-EC2 architecture (`i-01ad7da9373312642`), **Zero-downtime rolling deployment is NOT currently guaranteed**. A brief container restart window (~3s) occurs during updates.

---

## 2. Incident Severity Classification

| Severity Level | Definition | Impact | Response SLA |
| :--- | :--- | :--- | :--- |
| **SEV-1** | Complete Production Outage / Data Risk | Site down, DB unreachable, cross-tenant leak | < 15 minutes |
| **SEV-2** | Major Subsystem Outage | Matching/Scoring down, Webhooks failing | < 1 hour |
| **SEV-3** | Degraded Performance | Latency spike, Rate limit headroom reduced | < 4 hours |
| **SEV-4** | Minor Operational Issue | UI alignment artifact, log format warning | Next business day |

---

## 3. Operational Runbooks (20 Standard Scenarios)

### Scenario 1: Normal Deployment
- **Check**: Clean working tree, green local Pytest/Vitest suites.
- **Action**: Run `python3 sync_to_ec2.py` and restart containers via AWS SSM.
- **Validation**: Liveness = 200, Readiness = 200, Synthetic Heartbeat = 10/10 PASS.

### Scenario 2: Failed Deployment
- **Symptom**: Container unhealthy or heartbeat failure post-deploy.
- **Action**: Immediately trigger Rollback Procedure to previous commit.
- **Validation**: Verify container health restored.

### Scenario 3: Rollback Execution
- **Command**: `git checkout <previous_commit> && ./scripts/sync_to_ec2.sh`
- **Validation**: Confirm backend container healthy & heartbeat PASS.

### Scenario 4: Backend Container Unhealthy
- **Command**: `sudo docker restart hiring_backend_production`
- **Validation**: `GET /api/v1/health/readiness` returns HTTP 200.

### Scenario 5: Worker Container Unhealthy
- **Command**: `sudo docker restart hiring_worker_production`
- **Validation**: Check SQS task consumer status.

### Scenario 6: Frontend Container Unhealthy
- **Command**: `sudo docker restart hiring_frontend_production`
- **Validation**: HTTP 200 on `https://<domain>/login`.

### Scenario 7: Proxy Container Unhealthy
- **Command**: `sudo docker restart hiring_proxy_production`
- **Validation**: TLS handshake & reverse proxy forwarding OK.

### Scenario 8: Database Connection Timeout
- **Check**: PostgreSQL container / RDS instance health.
- **Action**: Restart Postgres container or verify connection pool settings.

### Scenario 9: Migration Failure
- **Guard**: Do NOT auto-downgrade schema without validation.
- **Action**: Restore pre-migration `pg_dump` backup inside isolated environment.

### Scenario 10: Gemini API Degraded
- **Guard**: System operates in fail-safe mode; deterministic scoring & ranking remain 100% functional.

### Scenario 11: Webhook Delivery Backlog
- **Action**: Inspect worker queue and retry endpoint status.

### Scenario 12: SIEM / External Audit Unavailable
- **Guard**: CloudWatch log sink operates independently; core API requests remain 100% unblocked.

### Scenario 13: CloudWatch Logging Spike
- **Action**: Inspect log group retention and metric alarm thresholds.

### Scenario 14: SQS Worker Backlog Spike
- **Action**: Scale worker concurrency or investigate stuck background task.

### Scenario 15: High CPU Utilization
- **Check**: `top` / `docker stats` on EC2 instance.

### Scenario 16: High Memory Usage
- **Check**: Container memory bounds & async event loop tasks.

### Scenario 17: High API Latency Spike
- **Check**: PostgreSQL index usage & query execution plans (`EXPLAIN ANALYZE`).

### Scenario 18: Security Incident / Rate Limit Spike
- **Action**: Inspect `GET /api/v1/operations/security-events` & block suspicious IP.

### Scenario 19: Backup Verification Failure
- **Action**: Re-run `scripts/verify_backup_restore.py` with fresh dump.

### Scenario 20: Disaster Recovery Execution
- **Action**: Follow `docs/runbooks/disaster-recovery.md` to restore into isolated PostgreSQL environment.
