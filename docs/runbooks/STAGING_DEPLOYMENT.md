# Azure Staging Environment Deployment Runbook

## Overview
This runbook documents the configuration, deployment pipeline, validation steps, and operational verification procedures for the isolated Azure Staging environment.

## Environment Isolation Architecture
- **Resource Group**: `rg-staging-eus`
- **Networking**: `vnet-staging` with isolated database subnet `snet-staging-db`.
- **Services**:
  - Azure PostgreSQL Flexible Server 16 (Staging instance with `pgvector`).
  - Azure Storage Account (`sastagingdocuments`) & Container (`staging-documents`).
  - Azure Service Bus Namespace (`sb-staging`) & Topic (`staging-application-events`).
  - Azure Cache for Redis (`redis-staging`).
  - Azure Key Vault (`kv-hiring-staging`).
  - Azure Container Apps (`app-staging-backend`, `app-staging-worker`, `app-staging-frontend`).

## Deployment Execution Steps
1. **Infrastructure Provisioning**:
   ```bash
   cd infra/terraform/environments/staging
   terraform init
   terraform plan -out=staging.tfplan
   terraform apply staging.tfplan
   ```
2. **Database Migration**:
   ```bash
   alembic upgrade head
   ```
3. **Secrets Population**:
   Store staging database credentials, JWT secrets, and `GEMINI_API_KEY` in Azure Key Vault `kv-hiring-staging`.

## Quality & Governance Verification
- **Zero Production Data**: Staging database operates exclusively on synthetic test data.
- **Tenant RLS Guard**: `FORCE ROW LEVEL SECURITY` active across all 19 PostgreSQL tables.
- **AI Governance**: Candidate scoring (9B) and ranking (9C) execute 100% deterministically with $0$ LLM token calls.
