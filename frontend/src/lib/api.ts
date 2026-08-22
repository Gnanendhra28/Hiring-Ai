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

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_platform_admin: boolean;
  is_active: boolean;
  is_verified: boolean;
}

export interface OrgMembership {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  role: "PLATFORM_ADMIN" | "ORGANIZATION_ADMIN" | "RECRUITER" | "CANDIDATE";
  status: "ACTIVE" | "SUSPENDED" | "INVITED";
}

export interface UserProfileData {
  user: AuthUser;
  memberships: OrgMembership[];
}

export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    return "";
  }
  return "http://localhost:8000";
}

export async function loginUser(email: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
  const baseUrl = getApiBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: null }));
      if (res.status === 401) {
        throw new Error("Invalid email address or password. Please try again.");
      }
      if (res.status === 403) {
        throw new Error("Your account has been deactivated or lacks access.");
      }
      throw new Error(err.detail || "Authentication failed. Please check your credentials.");
    }
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    setOrgId("");

    try {
      const meRes = await fetch(`${baseUrl}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      if (meRes.ok) {
        const meData = await meRes.json();
        if (meData.memberships && meData.memberships.length > 0 && meData.memberships[0].organization_id) {
          setOrgId(meData.memberships[0].organization_id);
        }
      }
    } catch {}

    return data;
  } catch (error: any) {
    if (error.name === "TypeError" || error.message.includes("fetch")) {
      throw new Error("Unable to connect to AuraHire. Check your connection and try again.");
    }
    throw error;
  }
}

export async function getGoogleAuthUrl(redirectUri?: string): Promise<{ url: string | null; configured: boolean }> {
  const baseUrl = getApiBaseUrl();
  try {
    const query = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : "";
    const res = await fetch(`${baseUrl}/api/v1/auth/google/url${query}`);
    if (!res.ok) return { url: null, configured: false };
    return res.json();
  } catch {
    return { url: null, configured: false };
  }
}

export async function googleAuthCallback(code: string, redirectUri?: string, requestedRole?: string): Promise<{ access_token: string; refresh_token: string }> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}/api/v1/auth/google/callback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, redirect_uri: redirectUri, requested_role: requestedRole }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: null }));
    throw new Error(err.detail || "Google authentication failed.");
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function registerUser(email: string, password: string, full_name: string): Promise<AuthUser> {
  const baseUrl = getApiBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: null }));
      if (res.status === 400 || res.status === 409) {
        throw new Error("This email is already registered. Try signing in instead.");
      }
      if (res.status === 422) {
        throw new Error("Please verify all fields. Password must be at least 8 characters.");
      }
      throw new Error(err.detail || "We couldn't create your account right now. Please try again.");
    }
    return res.json();
  } catch (error: any) {
    if (error.name === "TypeError" || error.message.includes("fetch")) {
      throw new Error("Unable to connect to AuraHire. Check your connection and try again.");
    }
    throw error;
  }
}

export async function registerCandidate(
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  phoneNumber: string
): Promise<AuthUser> {
  const baseUrl = getApiBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/v1/auth/register/candidate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        phone_number: phoneNumber,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: null }));
      if (res.status === 400 || res.status === 409) {
        throw new Error(err.detail || "This email is already registered. Try signing in instead.");
      }
      if (res.status === 422) {
        throw new Error("Please verify all fields. Phone number and 8-character password are required.");
      }
      throw new Error(err.detail || "We couldn't create your candidate account right now. Please try again.");
    }
    return res.json();
  } catch (error: any) {
    if (error.name === "TypeError" || error.message.includes("fetch")) {
      throw new Error("Unable to connect to AuraHire. Check your connection and try again.");
    }
    throw error;
  }
}

export async function registerEmployee(
  email: string,
  password: string,
  firstName: string,
  lastName: string,
  companyName?: string
): Promise<AuthUser> {
  const baseUrl = getApiBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/v1/auth/register/employee`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        company_name: companyName,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: null }));
      if (res.status === 400 || res.status === 409) {
        throw new Error("This email is already registered. Try signing in instead.");
      }
      if (res.status === 422) {
        throw new Error("Please verify all fields. Password must be at least 8 characters.");
      }
      throw new Error(err.detail || "We couldn't create your employee account right now. Please try again.");
    }
    return res.json();
  } catch (error: any) {
    if (error.name === "TypeError" || error.message.includes("fetch")) {
      throw new Error("Unable to connect to AuraHire. Check your connection and try again.");
    }
    throw error;
  }
}

export async function fetchUserProfile(): Promise<UserProfileData | null> {
  const res = await apiFetch("/api/v1/auth/me");
  if (!res.ok) return null;
  const data = await res.json();
  if (data.memberships && data.memberships.length > 0 && !getOrgId()) {
    setOrgId(data.memberships[0].organization_id);
  }
  return data;
}

export const getUserProfile = fetchUserProfile;

export interface CandidateProfileData {
  id?: string;
  user_id?: string;
  location?: string;
  headline?: string;
  summary?: string;
  phone?: string;
  photo_url?: string;
  degree?: string;
  college?: string;
  skills?: string[];
  experience?: any[];
  education?: any[];
  career_preferences?: Record<string, any>;
  languages?: any[];
  internships?: any[];
  projects?: any[];
  accomplishments?: Record<string, any>;
  employment?: any[];
  website_url?: string;
  linkedin_url?: string;
  resume_url?: string;
  resume_filename?: string;
  resume_filesize?: number;
  resume_updated_at?: string;
  created_at?: string;
}

export async function getCandidateProfile(): Promise<CandidateProfileData | null> {
  const res = await apiFetch("/api/v1/candidate/profile");
  if (!res.ok) return null;
  return res.json();
}

export async function updateCandidateProfile(data: Partial<CandidateProfileData>): Promise<CandidateProfileData> {
  const res = await apiFetch("/api/v1/candidate/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: null }));
    throw new Error(err.detail || "Failed to update candidate profile.");
  }
  return res.json();
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
    const isCandidateOrGlobalEndpoint =
      endpoint.includes("/auth/") ||
      endpoint.includes("/candidate") ||
      (endpoint.includes("/jobs") && !endpoint.includes("/recruiter/"));
    if (orgId && !headers.has("X-Organization-ID") && !isCandidateOrGlobalEndpoint) {
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

export interface FunnelConversionMetrics {
  application_to_eligible_pct: number;
  eligible_to_top_k_pct: number;
  top_k_to_reviewed_pct: number;
  reviewed_to_advanced_pct: number;
  advanced_to_offer_pct: number;
  offer_to_accepted_pct: number;
  accepted_to_hired_pct: number;
}

export interface DecisionAnalytics {
  decision_counts: { ADVANCE: number; REJECT: number; HOLD: number };
  decision_rates_pct: { advance_rate_pct: number; reject_rate_pct: number; hold_rate_pct: number };
  ai_recommendation_distribution: { RECOMMEND: number; REQUIRES_REVIEW: number; DO_NOT_RECOMMEND: number };
  ai_override_sample_size: number;
  ai_agreed_count: number;
  ai_overridden_count: number;
  ai_override_rate_pct: number;
  ai_override_note: string;
}

export interface ScoreAnalytics {
  average_score?: number;
  median_score?: number;
  highest_score?: number;
  lowest_score?: number;
  pass_count: number;
  fail_count: number;
  confidence_distribution: { HIGH: number; MEDIUM: number; LOW: number };
}

export interface OfferAnalytics {
  offers_extended: number;
  offers_accepted: number;
  offer_acceptance_rate_pct: number;
  avg_offer_to_acceptance_days?: number;
}

export interface RequisitionReport {
  requisition_id: string;
  organization_id: string;
  title: string;
  department?: string;
  location?: string;
  employment_type: string;
  job_status: string;
  created_at: string;
  closed_at?: string;
  active_intelligence_version?: number;
  intelligence_status?: string;
  intelligence_confidence?: number;
  total_applications: number;
  eligible_applications: number;
  ineligible_applications: number;
  top_k_candidates: number;
  candidates_reviewed: number;
  candidates_advanced: number;
  candidates_rejected: number;
  candidates_held: number;
  offers_extended: number;
  offers_accepted: number;
  candidates_hired: number;
  requisition_fill_status: string;
  funnel_conversion: FunnelConversionMetrics;
  decision_analytics: DecisionAnalytics;
  score_analytics: ScoreAnalytics;
  offer_analytics: OfferAnalytics;
  time_to_first_candidate_days?: number;
  time_to_first_review_days?: number;
  time_to_first_decision_days?: number;
  time_to_fill_days?: number;
  time_to_hire_days?: number;
}

export interface TenantRequisitionReport {
  organization_id: string;
  total_requisitions: number;
  requisition_status_counts: { DRAFT: number; PUBLISHED: number; PAUSED: number; CLOSED: number };
  total_applications_all_jobs: number;
  total_hired_all_jobs: number;
  avg_tenant_time_to_fill_days?: number;
  avg_tenant_time_to_hire_days?: number;
}

export async function fetchRequisitionReport(jobId: string): Promise<RequisitionReport | null> {
  const res = await apiFetch(`/api/v1/requisitions/${jobId}/report`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchTenantRequisitionReport(): Promise<TenantRequisitionReport | null> {
  const res = await apiFetch(`/api/v1/requisitions/report`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function exportRequisitionReportCSV(jobId: string): Promise<Response> {
  return await apiFetch(`/api/v1/requisitions/${jobId}/report/export`);
}

export interface OrganizationRequisitionPerformanceRow {
  requisition_id: string;
  title: string;
  status: string;
  department?: string;
  location?: string;
  employment_type: string;
  applications: number;
  eligible: number;
  reviewed: number;
  advanced: number;
  offers: number;
  hired: number;
  time_to_fill_days?: number;
  time_to_hire_days?: number;
  intelligence_status: string;
  created_at: string;
}

export interface OrganizationDashboard {
  organization_id: string;
  period_start?: string;
  period_end?: string;
  total_requisitions: number;
  open_requisitions: number;
  published_requisitions: number;
  paused_requisitions: number;
  closed_requisitions: number;
  filled_requisitions: number;
  total_applications: number;
  eligible_candidates: number;
  candidates_advanced: number;
  offers_extended: number;
  offers_accepted: number;
  candidates_hired: number;
  avg_time_to_fill_days?: number;
  avg_time_to_hire_days?: number;
  average_candidate_score?: number;
  pass_fail_distribution: { PASS: number; FAIL: number };
  confidence_distribution: { HIGH: number; MEDIUM: number; LOW: number };
  requisitions: OrganizationRequisitionPerformanceRow[];
}

export interface AuditAnalytics {
  organization_id: string;
  total_recruiter_decisions: number;
  advance_count: number;
  reject_count: number;
  hold_count: number;
  offer_extended_count: number;
  offer_accepted_count: number;
  candidate_hired_count: number;
  audit_trail_completeness_pct: number;
  decision_activity_by_requisition: Record<string, number>;
}

export interface AIGovernanceAnalytics {
  organization_id: string;
  ai_recommendations_generated: number;
  requires_review_count: number;
  recommendation_confidence_distribution: { HIGH: number; MEDIUM: number; LOW: number };
  recommendation_generation_failures: number;
  recommendation_avg_latency_ms?: number;
  recruiter_decisions_count: number;
  recommendation_override_count: number;
  ai_decision_authority: string;
}

export interface AITelemetry {
  organization_id: string;
  total_gemini_requests: number;
  successful_requests: number;
  failed_requests: number;
  retry_count: number;
  estimated_input_tokens: number;
  estimated_output_tokens: number;
  estimated_cost_usd: number;
  average_latency_ms?: number;
}

export async function fetchOrganizationDashboard(params?: {
  start_date?: string;
  end_date?: string;
  status?: string;
  department?: string;
  employment_type?: string;
  location?: string;
}): Promise<OrganizationDashboard | null> {
  const query = new URLSearchParams();
  if (params?.start_date) query.append("start_date", params.start_date);
  if (params?.end_date) query.append("end_date", params.end_date);
  if (params?.status) query.append("status", params.status);
  if (params?.department) query.append("department", params.department);
  if (params?.employment_type) query.append("employment_type", params.employment_type);
  if (params?.location) query.append("location", params.location);

  const url = `/api/v1/requisitions/dashboard${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await apiFetch(url);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchAuditAnalytics(params?: { start_date?: string; end_date?: string }): Promise<AuditAnalytics | null> {
  const query = new URLSearchParams();
  if (params?.start_date) query.append("start_date", params.start_date);
  if (params?.end_date) query.append("end_date", params.end_date);
  const url = `/api/v1/requisitions/audit-analytics${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await apiFetch(url);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchAIGovernanceAnalytics(params?: { start_date?: string; end_date?: string }): Promise<AIGovernanceAnalytics | null> {
  const query = new URLSearchParams();
  if (params?.start_date) query.append("start_date", params.start_date);
  if (params?.end_date) query.append("end_date", params.end_date);
  const url = `/api/v1/requisitions/ai-governance-analytics${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await apiFetch(url);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchAITelemetry(): Promise<AITelemetry | null> {
  const res = await apiFetch(`/api/v1/requisitions/ai-telemetry`);
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function exportOrganizationReportCSV(params?: {
  start_date?: string;
  end_date?: string;
  status?: string;
  department?: string;
  employment_type?: string;
  location?: string;
}): Promise<Response> {
  const query = new URLSearchParams();
  if (params?.start_date) query.append("start_date", params.start_date);
  if (params?.end_date) query.append("end_date", params.end_date);
  if (params?.status) query.append("status", params.status);
  if (params?.department) query.append("department", params.department);
  if (params?.employment_type) query.append("employment_type", params.employment_type);
  if (params?.location) query.append("location", params.location);

  const url = `/api/v1/requisitions/report/export${query.toString() ? `?${query.toString()}` : ""}`;
  return await apiFetch(url);
}

// ---------------------------------------------------------------------------
// Phase 20: Enterprise Webhook Management APIs
// ---------------------------------------------------------------------------

export interface WebhookSubscription {
  id: string;
  organization_id: string;
  endpoint_url: string;
  enabled: boolean;
  subscribed_events: string[];
  created_at: string;
  updated_at: string;
}

export interface WebhookSubscriptionCreateResponse extends WebhookSubscription {
  secret: string;
}

export interface SecretRotationResponse {
  subscription_id: string;
  new_secret: string;
}

export interface WebhookEventResponse {
  id: string;
  organization_id: string;
  subscription_id: string;
  event_id: string;
  event_type: string;
  delivery_status: string;
  attempt_count: number;
  first_attempt_at?: string;
  last_attempt_at?: string;
  delivered_at?: string;
  last_http_status?: number;
  last_error_code?: string;
  created_at: string;
}

export interface WebhookTestResponse {
  subscription_id: string;
  event_type: string;
  delivery_status: string;
  http_status?: number;
  delivered: boolean;
}

export async function fetchWebhookSubscriptions(): Promise<WebhookSubscription[]> {
  const res = await apiFetch("/api/v1/webhooks/subscriptions");
  if (res.ok) {
    return await res.json();
  }
  return [];
}

export async function createWebhookSubscription(data: {
  endpoint_url: string;
  subscribed_events: string[];
}): Promise<WebhookSubscriptionCreateResponse | null> {
  const res = await apiFetch("/api/v1/webhooks/subscriptions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function updateWebhookSubscription(
  subscriptionId: string,
  data: { endpoint_url?: string; enabled?: boolean; subscribed_events?: string[] }
): Promise<WebhookSubscription | null> {
  const res = await apiFetch(`/api/v1/webhooks/subscriptions/${subscriptionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function deleteWebhookSubscription(subscriptionId: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/webhooks/subscriptions/${subscriptionId}`, {
    method: "DELETE",
  });
  return res.ok || res.status === 204;
}

export async function rotateWebhookSecret(subscriptionId: string): Promise<SecretRotationResponse | null> {
  const res = await apiFetch(`/api/v1/webhooks/subscriptions/${subscriptionId}/rotate-secret`, {
    method: "POST",
  });
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function sendTestWebhook(subscriptionId: string): Promise<WebhookTestResponse | null> {
  const res = await apiFetch(`/api/v1/webhooks/subscriptions/${subscriptionId}/test`, {
    method: "POST",
  });
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function fetchWebhookDeliveryHistory(subscriptionId?: string): Promise<WebhookEventResponse[]> {
  const query = subscriptionId ? `?subscription_id=${encodeURIComponent(subscriptionId)}` : "";
  const res = await apiFetch(`/api/v1/webhooks/events${query}`);
  if (res.ok) {
    return await res.json();
  }
  return [];
}

// ---------------------------------------------------------------------------
// Phase 21: Enterprise Operations Observability APIs
// ---------------------------------------------------------------------------

export interface OperationsMetricsResponse {
  organization_id: string;
  system_health: {
    backend_status: string;
    worker_status: string;
    ai_service_status: string;
    database_status: string;
    container_restarts: number;
  };
  rate_limiting: {
    tenant_isolation: string;
    read_api_limit: string;
    state_change_limit: string;
    ai_api_limit: string;
    webhook_api_limit: string;
  };
  webhook_observability: {
    total_events: number;
    delivered: number;
    retrying: number;
    failed: number;
    success_rate_percent: number;
  };
  ai_observability: {
    total_requests: number;
    total_token_estimate: number;
    total_estimated_cost_usd: number;
    average_latency_seconds: number;
  };
  ai_governance: {
    ai_mutation_paths: number;
    recruiter_decision_authority: string;
  };
}

export async function fetchOperationsMetrics(): Promise<OperationsMetricsResponse | null> {
  const res = await apiFetch("/api/v1/operations/metrics");
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export interface SecurityEventsResponse {
  organization_id: string;
  siem_adapter: {
    status: string;
    provider: string;
    external_siem: string;
  };
  total_events: number;
  events: Array<{
    event_id: string;
    event_type: string;
    occurred_at: string;
    outcome: string;
    severity: string;
  }>;
}

export async function fetchSecurityEvents(): Promise<SecurityEventsResponse | null> {
  const res = await apiFetch("/api/v1/operations/security-events");
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export interface JobItemData {
  id: string;
  title: string;
  slug: string;
  description: string;
  department?: string;
  location?: string;
  employment_type: string;
  status: "DRAFT" | "PUBLISHED" | "PAUSED" | "CLOSED";
  verification_status: string;
  created_at: string;
  applications_count?: number;
  ai_shortlisted_count?: number;
  skills?: string[];
}

export async function fetchRecruiterJobs(): Promise<JobItemData[]> {
  const res = await apiFetch("/api/v1/jobs");
  if (res.ok) {
    const data = await res.json();
    return data.items || [];
  }
  return [];
}

export async function updateJobStatus(jobId: string, status: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  });
  return res.ok;
}

export async function deleteJobPost(jobId: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}`, {
    method: "DELETE",
  });
  return res.ok;
}

export interface RecruiterProfileData {
  id: string;
  user_id: string;
  job_title?: string;
  department?: string;
  phone_number?: string;
  company_name?: string;
  website_url?: string;
  registration_id?: string;
  linkedin_url?: string;
  verification_status: "UNVERIFIED" | "PENDING_VERIFICATION" | "APPROVED" | "VERIFIED";
  submitted_at?: string;
  created_at: string;
}

export async function fetchRecruiterProfile(): Promise<RecruiterProfileData | null> {
  const res = await apiFetch("/api/v1/auth/recruiter/profile");
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function updateRecruiterProfile(payload: Partial<RecruiterProfileData>): Promise<RecruiterProfileData | null> {
  const res = await apiFetch("/api/v1/auth/recruiter/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function submitEmployerVerification(): Promise<RecruiterProfileData | null> {
  const res = await apiFetch("/api/v1/auth/recruiter/profile/submit-verification", {
    method: "POST",
  });
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export interface PendingEmployerVerification {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  job_title?: string;
  department?: string;
  phone_number?: string;
  company_name?: string;
  website_url?: string;
  registration_id?: string;
  linkedin_url?: string;
  verification_status: string;
  submitted_at?: string;
}

export async function fetchPendingEmployers(): Promise<PendingEmployerVerification[]> {
  const res = await apiFetch("/api/v1/admin/employers/pending");
  if (res.ok) {
    return await res.json();
  }
  return [];
}

export async function verifyEmployerProfile(userId: string, action: "APPROVE" | "REJECT"): Promise<boolean> {
  const res = await apiFetch(`/api/v1/admin/employers/${userId}/verify?action=${action}`, {
    method: "POST",
  });
  return res.ok;
}

export async function fetchPendingJobsAdmin(): Promise<JobItemData[]> {
  const res = await apiFetch("/api/v1/admin/jobs/pending");
  if (res.ok) {
    const data = await res.json();
    return data.items || [];
  }
  return [];
}

export async function fetchAllJobsAdmin(verificationStatus?: string): Promise<JobItemData[]> {
  const url = verificationStatus
    ? `/api/v1/admin/jobs?page_size=5000&verification_status=${verificationStatus}`
    : "/api/v1/admin/jobs?page_size=5000";
  const res = await apiFetch(url);
  if (res.ok) {
    const data = await res.json();
    return data.items || [];
  }
  return [];
}

export async function verifyJobAdmin(jobId: string, action: "APPROVE" | "REJECT", rejectionReason?: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/admin/jobs/${jobId}/verify`, {
    method: "POST",
    body: JSON.stringify({ action, rejection_reason: rejectionReason || "Does not meet platform compliance standard." }),
  });
  return res.ok;
}

export async function deleteJobAdmin(jobId: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/admin/jobs/${jobId}`, {
    method: "DELETE",
  });
  return res.ok;
}

export async function batchDeleteJobsAdmin(jobIds: string[]): Promise<boolean> {
  const res = await apiFetch("/api/v1/admin/jobs/batch-delete", {
    method: "POST",
    body: JSON.stringify({ job_ids: jobIds }),
  });
  return res.ok;
}

export async function createAdminAccount(fullName: string, email: string, password: string): Promise<{ success: boolean; message: string }> {
  const res = await apiFetch("/api/v1/admin/add-admin", {
    method: "POST",
    body: JSON.stringify({ full_name: fullName, email, password }),
  });
  if (res.ok) {
    const data = await res.json();
    return { success: true, message: data.message || "Successfully created Platform Admin account." };
  }
  const err = await res.json().catch(() => ({ detail: null }));
  return { success: false, message: err.detail || "Failed to create Admin account." };
}

export async function fetchApprovedEmployers(): Promise<PendingEmployerVerification[]> {
  const res = await apiFetch("/api/v1/admin/employers/approved");
  if (res.ok) {
    return await res.json();
  }
  return [];
}

export async function deleteEmployerProfile(userId: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/admin/employers/${userId}`, {
    method: "DELETE",
  });
  return res.ok;
}

export interface AdminAnalyticsData {
  approved_employers_count: number;
  pending_employers_count: number;
  total_employers_count: number;
  employer_approval_rate: number;
  approved_jobs_count: number;
  pending_jobs_count: number;
  active_jobs_count: number;
  total_jobs_count: number;
  job_approval_rate: number;
  total_applications_count: number;
  shortlisted_applications_count: number;
  system_health: string;
  last_updated: string;
}

export async function fetchAdminAnalytics(): Promise<AdminAnalyticsData | null> {
  const res = await apiFetch("/api/v1/admin/analytics");
  if (res.ok) {
    return await res.json();
  }
  return null;
}

export async function submitJobForAdminApproval(jobId: string): Promise<boolean> {
  const res = await apiFetch(`/api/v1/jobs/${jobId}`, {
    method: "PATCH",
    body: JSON.stringify({ verification_status: "PENDING_VERIFICATION" }),
  });
  return res.ok;
}

export async function requestForgotPassword(
  email: string,
  portalType?: "CANDIDATE" | "EMPLOYEE"
): Promise<{ success: boolean; message: string; dev_otp_hint?: string }> {
  const res = await apiFetch("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email, portal_type: portalType }),
  });
  const data = await res.json().catch(() => ({ detail: null }));
  if (res.ok) {
    return { success: true, message: data.message || "Password recovery code sent.", dev_otp_hint: data.dev_otp_hint };
  }
  return { success: false, message: data.detail || "Failed to initiate password recovery." };
}

export async function resetPassword(email: string, newPassword: string, resetCode?: string): Promise<{ success: boolean; message: string }> {
  const res = await apiFetch("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify({ email, new_password: newPassword, reset_code: resetCode }),
  });
  const data = await res.json().catch(() => ({ detail: null }));
  if (res.ok) {
    return { success: true, message: data.message || "Password successfully reset." };
  }
  return { success: false, message: data.detail || "Failed to reset password." };
}




