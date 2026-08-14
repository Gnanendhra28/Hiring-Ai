# ADR 016: Phase 12 Production Cloud Infrastructure & Deployment Integration

## Context & Problem Statement
Transitioning the AI Hiring Platform from a production-ready application to a cloud-deployable production system requires establishing infrastructure-as-code (IaC), cloud provider service integration (Azure Service Bus, Azure Blob Storage, Azure Key Vault, Azure Cache for Redis), multi-stage CD deployment pipelines, and non-destructive smoke testing while strictly preserving provider isolation, local development, 100% deterministic candidate scoring/ranking, and AI governance (**"AI ASSISTS. RECRUITER DECIDES."**).

## Architectural Decisions Implemented

### 1. Provider-Isolated Cloud Infrastructure Adapters
- **Event Bus**: Implemented `AzureServiceBusEventBus` in [`backend/app/infrastructure/events/service_bus.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/infrastructure/events/service_bus.py) implementing `EventBus`.
- **Distributed Rate Limiting**: Implemented `RedisRateLimiterAdapter` in [`backend/app/core/rate_limiter.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/rate_limiter.py) implementing `IRateLimiterProvider` with automatic fallback to `InMemoryRateLimiterAdapter`.
- **Secret Management**: Implemented `SecretProvider` in [`backend/app/core/secrets.py`](file:///Users/gnanendhrajoy/Desktop/Hiring%20AI/backend/app/core/secrets.py) with `EnvironmentSecretProvider` and `AzureKeyVaultSecretProvider`.

### 2. Terraform Infrastructure as Code (`infra/terraform/`)
- Created modular Terraform specifications in `infra/terraform/` (`main.tf`, `variables.tf`, `outputs.tf`, `terraform.tfvars.example`).
- Provisions Azure Resource Group, Virtual Network & Subnets, Azure Container Registry (ACR), Azure PostgreSQL Flexible Server with `pgvector`, Azure Blob Storage, Azure Service Bus, and Azure Key Vault.

### 3. CD Deployment Pipeline & Production Approval Gate (`.github/workflows/deploy.yml`)
- Created multi-stage deployment pipeline in `.github/workflows/deploy.yml`:
  `Lint & Tests` -> `Container Build` -> `Staging Deployment` -> `Production Approval Gate` -> `Production Deployment`.

### 4. Non-Destructive Production Smoke Test Suite (`backend/tests/test_phase12_smoke.py`)
- Added non-destructive smoke test module verifying `/live`, `/ready`, `/metrics`, and `/api/v1/jobs` endpoints.

## Verification Summary
- **Backend Quality Gate**: **116 / 116 backend tests passing** ($100\%$), 0 `ruff` lint errors.
- **Frontend Quality Gate**: TypeScript typecheck passed, 0 ESLint warnings, Next.js 14 production build completed successfully.
- **Cloud Provisioning Note**: Infrastructure code and deployment artifacts validated locally; actual cloud resource creation requires deployment credentials.
