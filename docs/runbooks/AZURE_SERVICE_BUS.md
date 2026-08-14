# Azure Service Bus Production Runbook

## Overview
Defines Azure Service Bus setup, topic configurations, and `PipelineWorker` subscription handling.

## Topic & Filter Architecture
- **Topic Name**: `application-events`
- **Subscriptions**: `pipeline-worker-sub`
- **Application Properties**: `event_type`, `event_version`, `organization_id`, `aggregate_id`
- **Security**: Access controlled via Azure Managed Identity / SAS connection strings.
- **Payload Policy**: Payload contains domain IDs and correlation UUIDs only. Zero raw resume text or PII.
