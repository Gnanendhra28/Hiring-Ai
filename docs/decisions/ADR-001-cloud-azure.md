# ADR-001: Selection of Microsoft Azure as Primary Cloud Platform

## Status
Approved

## Context
The platform requires an enterprise-ready, scalable, and secure cloud infrastructure capable of hosting multi-tenant web portals, asynchronous background processing workers, relational and vector database storage, file storage for resumes, and AI model orchestration.

## Decision
We select **Microsoft Azure** as the primary cloud provider running on **Python 3.13** runtime environments. Key services chosen include:
- **Azure Container Apps (ACA)**: Microservice container deployment with scale-to-zero capabilities.
- **Azure Database for PostgreSQL**: Managed relational database with `pgvector` and Row Level Security (RLS) support.
- **Azure Blob Storage**: Secure document and resume binary storage using structured tenant pathing.
- **Azure Service Bus**: Enterprise queueing and publish-subscribe topic event bus with selective session support.
- **Azure Key Vault**: Hardware Security Module (HSM)-backed secret management. All production deployments MUST fetch secrets from Azure Key Vault and fail fast if default/development credentials are present.

## Consequences
- **Positive**: Native enterprise compliance (SOC 2, ISO 27001, HIPAA), seamless integration with Entra ID, and simplified compliance for global clients.
- **Negative**: Vendor lock-in risk for cloud-specific features.
- **Mitigation**: All cloud services are wrapped behind application-level abstraction adapters (`EventBus`, `ObjectStorageAdapter`, `SecretManagerAdapter`).
