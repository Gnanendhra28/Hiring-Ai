# ADR-008: Next.js 14.2.x Frontend Architecture, Recruiter UX & Real-Data Policy

## Status
Approved

## Context
The platform requires a production-grade, responsive, enterprise frontend. A common failure in AI SaaS platforms is visually overwhelming users with decorative 3D elements or presenting static, simulated UI data without real backend integration.

## Decision
1. **Next.js 14.2.x Foundation**: Selected Next.js 14.2.23 with React 18 for production stability, App Router features, and TanStack Query state synchronization.
2. **Selective 3D Policy**: Three.js / React Three Fiber is reserved strictly for high-impact visual models (landing page hero, candidate-job matching graph, recruitment pipeline funnel, architecture overview). Dense data tables, forms, and review tools MUST remain ultra-clean 2D components.
3. **Recruiter Job Workspace UX**: The Job Workspace is established as the primary recruiter hub containing sub-tab views (Overview, Applications, AI Ranking, Shortlisted, Assessments, Interviews, Offers, Communications, Analytics).
4. **No-Fake Data Policy**: Production UI displays real backend state only. Skeletons indicate active processing, empty states reflect zero data, and error banners report real API failures. Synthetic fixtures are restricted strictly to automated local test suites.

## Consequences
- Exceptional user experience, high performance, enterprise usability, and explainable AI candidate evaluation views.
