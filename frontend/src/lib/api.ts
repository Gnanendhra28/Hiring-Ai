/**
 * Hiring AI SaaS Platform - Production Frontend API Client & Auth Interceptor
 * Features:
 * - Bearer token & X-Organization-ID injection
 * - Automatic HTTP 401 token refresh via POST /api/v1/auth/refresh
 * - Single-flight refresh deduplication for concurrent 401 requests
 * - Strict single-retry guard (max 1 retry per original request)
 * - Anti-loop protection (prevents /auth/refresh from triggering recursive refresh)
 * - HTTP 403 isolation (403 forbidden does not trigger refresh)
 * - Safe SSR execution & localStorage token persistence
 */

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const ORG_ID_KEY = "organization_id";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(ORG_ID_KEY);
}

export function getOrgId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ORG_ID_KEY);
}

export function setOrgId(orgId: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ORG_ID_KEY, orgId);
}

export function logoutAndRedirect(redirectUrl = "/login"): void {
  clearTokens();
  if (typeof window !== "undefined" && window.location.pathname !== redirectUrl) {
    window.location.href = redirectUrl;
  }
}

let refreshPromise: Promise<string | null> | null = null;

export async function performTokenRefresh(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      logoutAndRedirect();
      return null;
    }

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "";
      const refreshUrl = `${baseUrl}/api/v1/auth/refresh`;

      // Raw fetch call to prevent recursive refresh loops
      const response = await fetch(refreshUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.status === 200) {
        const data = await response.json();
        if (data.access_token && data.refresh_token) {
          setTokens(data.access_token, data.refresh_token);
          return data.access_token;
        }
      }

      // If refresh fails (HTTP 401/403/400/500), clear auth state & redirect
      logoutAndRedirect();
      return null;
    } catch {
      logoutAndRedirect();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export interface ApiFetchOptions extends RequestInit {
  skipAuth?: boolean;
}

export async function apiFetch(
  endpoint: string,
  options: ApiFetchOptions = {},
  isRetry = false
): Promise<Response> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "";
  const url = endpoint.startsWith("http") ? endpoint : `${baseUrl}${endpoint}`;

  const headers = new Headers(options.headers || {});

  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (!options.skipAuth) {
    const token = getAccessToken();
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const orgId = getOrgId();
    if (orgId && !headers.has("X-Organization-ID")) {
      headers.set("X-Organization-ID", orgId);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle HTTP 401 Unauthorized
  if (response.status === 401) {
    // 1. Strict Retry Guard: If this request is already a retry, do not retry again!
    if (isRetry) {
      logoutAndRedirect();
      return response;
    }

    // 2. Anti-Loop Protection: Do not refresh if login or refresh endpoint returns 401
    const isAuthEndpoint =
      endpoint.includes("/auth/login") || endpoint.includes("/auth/refresh");
    if (isAuthEndpoint) {
      if (endpoint.includes("/auth/refresh")) {
        logoutAndRedirect();
      }
      return response;
    }

    // 3. Single-Flight Token Refresh
    const newAccessToken = await performTokenRefresh();

    if (newAccessToken) {
      // 4. Retry original request ONCE with new access token
      const retryHeaders = new Headers(options.headers || {});
      if (options.body && typeof options.body === "string" && !retryHeaders.has("Content-Type")) {
        retryHeaders.set("Content-Type", "application/json");
      }
      retryHeaders.set("Authorization", `Bearer ${newAccessToken}`);
      const orgId = getOrgId();
      if (orgId && !retryHeaders.has("X-Organization-ID")) {
        retryHeaders.set("X-Organization-ID", orgId);
      }

      return apiFetch(
        endpoint,
        {
          ...options,
          headers: retryHeaders,
        },
        true // Set isRetry = true for the single allowed retry
      );
    } else {
      return response;
    }
  }

  // HTTP 403 Forbidden does NOT trigger refresh
  return response;
}

// ============================================================================
// Strongly-Typed API Client Methods for Recruiter Candidate Matching & Intelligence
// ============================================================================

export interface JobIntelligenceData {
  id: string;
  job_id: string;
  version_number: number;
  status: "DRAFT" | "PROCESSING" | "COMPLETED" | "FAILED" | "STALE";
  ai_provider?: string;
  model_name?: string;
  embedding_model?: string;
  overall_confidence: number;
  created_at: string;
}

export interface CandidateRankingItem {
  id: string;
  rank_position: number;
  candidate_id: string;
  application_id?: string;
  score: number;
  score_confidence: number;
  eligibility_status: "PASS" | "FAIL" | "UNKNOWN";
  is_top_k: boolean;
  candidate_job_score_id: string;
  job_intelligence_version_id: string;
}

export interface CandidateRankingVersion {
  id: string;
  job_id: string;
  job_intelligence_version_id: string;
  ranking_version: number;
  top_k: number;
  status: string;
  candidate_count: number;
  eligible_candidate_count: number;
  ineligible_candidate_count: number;
  created_at: string;
  rankings: CandidateRankingItem[];
}

export interface CandidateFactorScore {
  id: string;
  factor_type: string;
  raw_score: number;
  configured_weight: number;
  normalized_weight: number;
  weighted_contribution: number;
  is_applicable: boolean;
  reason?: string;
}

export interface CandidateHardRequirementResult {
  id: string;
  requirement_id: string;
  status: string;
  candidate_value?: string;
  required_value?: string;
  operator?: string;
  reason?: string;
  confidence: number;
  evidence_text?: string;
}

export interface CandidateJobScoreData {
  id: string;
  organization_id: string;
  job_id: string;
  candidate_id: string;
  eligibility_status: "PASS" | "FAIL" | "UNKNOWN";
  overall_score: number;
  score_confidence: number;
  confidence_tier: "HIGH" | "MEDIUM" | "LOW";
  status: string;
  calculated_at: string;
}

export interface ScoreBreakdownDetail {
  score: CandidateJobScoreData;
  factor_scores: CandidateFactorScore[];
  hard_requirement_results: CandidateHardRequirementResult[];
}

export interface RequirementMatchData {
  id: string;
  job_requirement_id: string;
  requirement_type: string;
  raw_required_value: string;
  canonical_required_value: string;
  requirement_level: "REQUIRED" | "PREFERRED" | string;
  hard_constraint: boolean;
  match_status: "MATCHED" | "NOT_MATCHED" | "UNKNOWN" | "PROTECTED_EXCLUDED" | string;
  candidate_value?: string;
  normalized_candidate_value?: string;
  confidence: number;
  reason?: string;
  evidence_text?: string;
  evidence_verification_status: string;
}

export interface SemanticMatchData {
  id: string;
  query_context: string;
  candidate_context: string;
  similarity_score: number;
  embedding_model: string;
}

export interface CandidateJobMatchData {
  id: string;
  job_id: string;
  candidate_id: string;
  status: string;
  total_requirements_count: number;
  matched_requirements_count: number;
  hard_requirements_failed_count: number;
  overall_confidence: number;
}

export interface FeatureMatchDetail {
  match: CandidateJobMatchData;
  requirement_matches: RequirementMatchData[];
  semantic_matches: SemanticMatchData[];
}

export interface RecommendationReason {
  id: string;
  reason_code: string;
  reason_type: "POSITIVE" | "NEGATIVE" | string;
  description: string;
  evidence_reference?: string;
}

export interface RecommendationData {
  id: string;
  job_id: string;
  candidate_id: string;
  recommendation_type: "REQUIRES_REVIEW" | "ADVANCE" | "REJECT" | string;
  recommendation_confidence: number;
  status: string;
  summary: string;
  strengths: string[];
  gaps: string[];
  created_at: string;
}

export interface RecommendationDetail {
  recommendation: RecommendationData;
  reasons: RecommendationReason[];
  evidence: any[];
}

export interface DecisionAuditItem {
  id: string;
  job_id: string;
  candidate_id: string;
  application_id: string;
  decision: "ADVANCE" | "REJECT" | "HOLD" | string;
  previous_state: string;
  new_state: string;
  decision_reason: string;
  decided_by_user_id: string;
  decided_at: string;
}

export interface ApplicationDetail {
  id: string;
  job_id: string;
  candidate_id: string;
  candidate_name?: string;
  candidate_email?: string;
  headline?: string;
  skills?: string[];
  status: "SUBMITTED" | "RECRUITER_REVIEW" | "SHORTLISTED" | "REJECTED" | "DECIDED" | string;
  review_state?: string;
  decision?: string;
  decision_reason?: string;
  submitted_at?: string;
  created_at?: string;
}

// API Call Helpers

export async function fetchJobIntelligence(jobId: string): Promise<JobIntelligenceData | null> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/intelligence`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchActiveRankings(jobId: string): Promise<CandidateRankingVersion | null> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/rankings/active`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchScoreBreakdown(jobId: string, candidateId: string): Promise<ScoreBreakdownDetail | null> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/scoring/${candidateId}/breakdown`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchFeatureMatchDetail(jobId: string, candidateId: string): Promise<FeatureMatchDetail | null> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/matching/features/${candidateId}`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchRecommendationDetail(jobId: string, candidateId: string): Promise<RecommendationDetail | null> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/recommendations/${candidateId}`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchDecisionHistory(jobId: string, appId: string): Promise<DecisionAuditItem[]> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}/decision-history`);
  if (res.ok) {
    return await res.json();
  }
  return [];
}

export async function submitRecruiterDecision(
  jobId: string,
  appId: string,
  decision: "ADVANCE" | "REJECT" | "HOLD",
  reason: string
): Promise<Response> {
  return await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}/decision`, {
    method: "POST",
    body: JSON.stringify({
      decision,
      decision_reason: reason,
    }),
  });
}

export interface CandidatePlacement {
  id: string;
  organization_id: string;
  job_id: string;
  candidate_id: string;
  application_id: string;
  offer_status: "NOT_CREATED" | "OFFER_EXTENDED" | "OFFER_ACCEPTED" | "OFFER_REJECTED" | "HIRED";
  offer_created_at?: string;
  offer_accepted_at?: string;
  placed_at?: string;
  created_by_user_id?: string;
  notes?: string;
  time_to_fill_days?: number;
  time_to_hire_days?: number;
}

export async function fetchCandidatePlacement(jobId: string, appId: string): Promise<CandidatePlacement | null> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}/placement`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function createCandidateOffer(jobId: string, appId: string, notes?: string): Promise<Response> {
  return await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}/offer/create`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export async function acceptCandidateOffer(jobId: string, appId: string, notes?: string): Promise<Response> {
  return await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}/offer/accept`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export async function completeCandidateHire(jobId: string, appId: string, notes?: string): Promise<Response> {
  return await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}/placement/hire`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}


