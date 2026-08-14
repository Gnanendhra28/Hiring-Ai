# Azure Blob Storage Production Runbook

## Overview
Defines production candidate document storage management, container security, and tenant path isolation.

## Security & Path Structure
- Container: `documents` (Private access, public access disabled).
- Blob Path Layout: `organizations/{organization_id}/documents/{document_id}/{filename}`
- Verification: `StorageAdapter` verifies candidate document tenant ownership before reading or serving blob content.
