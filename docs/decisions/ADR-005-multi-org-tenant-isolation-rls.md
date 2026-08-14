# ADR-005: Multi-Organization Identity & PostgreSQL Row Level Security (RLS) Strategy

## Status
Approved

## Context
In a multi-tenant recruitment platform, recruiters or hiring managers may belong to multiple organizations. Exposing data across tenant boundaries is a critical security violation. Relying solely on application-level filtering (`WHERE organization_id = ...`) is insufficient for complete security depth.

## Decision
1. **Multi-Organization Model**: Users can hold active memberships in multiple organizations. The active tenant scope is requested via the `X-Organization-ID` header.
2. **Backend Context Verification**: Middleware verifies user membership in the requested organization before allowing request execution.
3. **Database RLS Session Strategy**: For every database transaction, the unit-of-work connection executes:
   ```sql
   SET LOCAL app.current_organization_id = '<active_organization_id>';
   ```
4. **PostgreSQL RLS Policies**: Database tables (`jobs`, `applications`, `documents`, etc.) enforce RLS policies that evaluate `current_setting('app.current_organization_id', true)`.

## Consequences
- Guaranteed defense-in-depth data isolation at the database engine level.
- Unverified `organization_id` values passed by clients are rejected before reaching database queries.
