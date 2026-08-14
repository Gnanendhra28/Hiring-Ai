# Cloud Disaster Recovery Runbook

## Service Objectives
- **Recovery Point Objective (RPO)**: < 1 Hour
- **Recovery Time Objective (RTO)**: < 4 Hours

## Recovery Procedures
1. **Regional Azure Outage**: Trigger geo-redundant database failover in Azure Portal. Update connection string secret in Azure Key Vault.
2. **Event Queue Backlog**: Scale container app worker replicas (`PipelineWorker`) horizontally. Unique database constraints enforce idempotency.
3. **AI Gateway Outage**: System continues serving deterministic candidate scoring and ranking without disruption (`ai_provider: degraded`).
