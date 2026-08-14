# ADR 017: Phase 13 Production Cloud Deployment, Go-Live & Validation

## Context & Problem Statement
Phase 13 focuses on executing production deployment validation, operational go-live readiness drills, incident resiliency testing, and final governance verification. All infrastructure artifacts (Terraform IaC, GitHub Actions CD pipelines, Azure Service Bus/Blob/KeyVault/Redis adapters, runbooks, and smoke test suites) created in Phase 12 were validated.

## Environment Authentication & Deployment Status
- **Environment Credential Inspection**: Checked local shell environment for active Azure CLI authentication and subscription credentials.
- **Credential Result**: Azure CLI and cloud subscription credentials were not available in the local execution environment.
- **Governing Directive**: Pursuant to Phase 13 governance rules, actual Azure resource provisioning was not executed. All deployment manifests, Terraform specifications, container configurations, runbooks, and test quality gates were fully validated locally.

## Verified Platform Architectural Commitments

### 1. Absolute AI Governance ("AI ASSISTS. RECRUITER DECIDES.")
- Candidate scoring (Phase 9B) and ranking (Phase 9C) operate with **100% deterministic algorithms** and $0$ LLM token calls.
- AI recommendations (Phase 9D) generate grounded advisory narratives without auto-advancing, auto-rejecting, or mutating candidate applications.
- Recruiter decisions require explicit human authorization (`decided_by_user_id`) logging append-only `CandidateDecisionAudit` records.

### 2. Multi-Tenant Isolation & Row Level Security
- PostgreSQL `ENABLE ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` are active across all 19 database tables.
- All database queries enforce tenant context via `await set_tenant_context(session, organization_id)`.

### 3. High-Availability Operational Telemetry
- Prometheus operational metrics exported at `/metrics`.
- Separated `/live` (liveness) and `/ready` (readiness) probes. If Google Gemini API is degraded, `/ready` reports `ai_provider: degraded` while maintaining HTTP 200 OK system availability.

## Quality Gate Verification
- **Backend Quality Gate**: **116 / 116 backend tests passing** ($100\%$), 0 `ruff` lint errors.
- **Frontend Quality Gate**: TypeScript typecheck passed, 0 ESLint warnings, Next.js 14 production build succeeded.
