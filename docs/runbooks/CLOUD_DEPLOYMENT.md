# Azure Cloud Deployment Runbook

## Overview
This runbook details Azure cloud infrastructure deployment using Terraform and GitHub Actions CD pipelines for both Staging and Production environments.

## Environment Separation & Gate Governance
- **Staging Deployment**: Target `infra/terraform/environments/staging/`. Deploys isolated container instances, storage accounts, Redis caches, Key Vaults, and Service Bus namespaces. Consumes synthetic data exclusively.
- **Production Deployment**: Requires explicit manual approval in GitHub Actions (`.github/workflows/deploy.yml`).

## Provisioning Sequence
1. **Terraform Initialization & Inspection**:
   ```bash
   cd infra/terraform/environments/staging
   terraform init
   terraform plan -out=staging.tfplan
   # Inspect plan for zero unexpected resource destruction
   terraform apply staging.tfplan
   ```
2. **Secrets Storage**:
   Upload environment DB credentials and `GEMINI_API_KEY` to environment-specific Azure Key Vault.
3. **Database Migration**:
   Run `alembic upgrade head` from deployment worker container.
4. **Service Bus Configuration**:
   Provision `application-events` topic and subscriptions.
