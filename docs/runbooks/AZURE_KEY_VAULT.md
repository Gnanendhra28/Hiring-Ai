# Azure Key Vault Production Runbook

## Overview
Defines production secret storage, Access Policy / RBAC roles, and `AzureKeyVaultSecretProvider` integration.

## Managed Secrets
- `DATABASE-URL`
- `SECRET-KEY`
- `ENCRYPTION-KEY`
- `GEMINI-API-KEY`
- `AZURE-SERVICE-BUS-CONNECTION-STRING`

## Integration Policy
`AzureKeyVaultSecretProvider` fetches production secrets at app startup. In development/testing environments, `EnvironmentSecretProvider` reads from local environment settings.
