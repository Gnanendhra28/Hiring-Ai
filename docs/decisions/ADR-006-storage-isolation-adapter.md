# ADR-006: Object Storage Pathing & Tenant Ownership Adapter Validation

## Status
Approved

## Context
Uploaded candidate resumes, job documents, and generated artifacts are stored in Azure Blob Storage. Storing files with unstructured or non-isolated paths risks cross-tenant data access.

## Decision
1. **Structured Storage Paths**: All object storage keys enforce structured tenant hierarchy:
   - `organizations/{organization_id}/jobs/{job_id}/...`
   - `organizations/{organization_id}/candidates/{candidate_id}/...`
   - `organizations/{organization_id}/applications/{application_id}/...`
   - `organizations/{organization_id}/documents/{document_id}/{filename}`
2. **Adapter Ownership Validation**: The `ObjectStorageAdapter` validates that the target `organization_id` matches the authenticated context before performing write, read, or presigned URL generation.
3. **No Binary Blobs in PostgreSQL**: Database tables store document metadata and storage keys, never binary file payloads.

## Consequences
- Clean storage hierarchy, robust security boundaries, and simple lifecycle policy management in Azure Blob Storage.
