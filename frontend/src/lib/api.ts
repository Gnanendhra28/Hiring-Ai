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
