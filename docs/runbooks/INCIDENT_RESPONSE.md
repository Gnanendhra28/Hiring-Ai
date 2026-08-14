# Incident Response Runbook

## Incident Severity Levels
- **SEV-1 (Critical)**: Total database outage, complete application downtime, or security breach.
- **SEV-2 (High)**: Core features unavailable for an entire tenant or organization.
- **SEV-3 (Medium)**: Degradation of non-critical features (e.g. Gemini AI advisory narratives unavailable; scoring and ranking remain operational).

## Incident Response Steps
1. **Identify**: Monitor structured logs and `/metrics` for spike in 5xx HTTP responses or worker dead-letter logs.
2. **Contain**: Isolate affected components or toggle AI provider feature flags.
3. **Remediate**: Apply hotfix, failover DB, or roll back container tag.
4. **Post-Mortem**: Document root cause, timeline, impact, and preventive actions.
