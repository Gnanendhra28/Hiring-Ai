import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  apiFetch,
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  setOrgId,
  getOrgId,
  logoutAndRedirect,
} from "./api";

// Mock localStorage for JSDOM / Node environment
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
});

describe("Frontend API Client & Auth Refresh Interceptor", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.restoreAllMocks();
    // Setup window.location mock
    Object.defineProperty(global, "window", {
      value: {
        location: {
          href: "http://localhost/",
          pathname: "/",
        },
      },
      writable: true,
    });
  });

  // 1. Normal authenticated API request
  it("1. includes Bearer token and X-Organization-ID on normal authenticated request", async () => {
    setTokens("test_access_token", "test_refresh_token");
    setOrgId("test_org_123");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true }), { status: 200 })
    );
    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/jobs");
    expect(res.status).toBe(200);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/v1/jobs");
    const headers = options.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer test_access_token");
    expect(headers.get("X-Organization-ID")).toBe("test_org_123");
  });

  // 2. HTTP 401 triggers refresh & 3. Successful refresh retries original request & 9. New access token used
  it("2, 3, 9. triggers refresh on 401, updates token, and retries original request once", async () => {
    setTokens("old_access_token", "valid_refresh_token");

    const fetchMock = vi.fn()
      // First call (original request) returns 401
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Token expired" }), { status: 401 }))
      // Second call (refresh endpoint) returns new tokens
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            access_token: "new_access_token_999",
            refresh_token: "new_refresh_token_999",
            token_type: "bearer",
          }),
          { status: 200 }
        )
      )
      // Third call (retry original request) returns 200
      .mockResolvedValueOnce(new Response(JSON.stringify({ data: "success" }), { status: 200 }));

    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/jobs");
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(3);

    // Call 1: Original request with old token
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/jobs");
    expect((fetchMock.mock.calls[0][1].headers as Headers).get("Authorization")).toBe("Bearer old_access_token");

    // Call 2: Refresh request with refresh token
    expect(fetchMock.mock.calls[1][0]).toContain("/api/v1/auth/refresh");
    expect(fetchMock.mock.calls[1][1].body).toBe(JSON.stringify({ refresh_token: "valid_refresh_token" }));

    // Call 3: Retried request with new access token
    expect(fetchMock.mock.calls[2][0]).toContain("/api/v1/jobs");
    expect((fetchMock.mock.calls[2][1].headers as Headers).get("Authorization")).toBe("Bearer new_access_token_999");

    // Tokens updated in localStorage
    expect(getAccessToken()).toBe("new_access_token_999");
    expect(getRefreshToken()).toBe("new_refresh_token_999");
  });

  // 4. Failed refresh logs the user out
  it("4. clears auth state and redirects to /login if refresh fails", async () => {
    setTokens("expired_access_token", "invalid_refresh_token");

    const fetchMock = vi.fn()
      // Original request returns 401
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Expired" }), { status: 401 }))
      // Refresh request returns 401
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Invalid refresh token" }), { status: 401 }));

    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/jobs");
    expect(res.status).toBe(401);

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  // 5. Refresh endpoint does not recursively trigger refresh
  it("5. does not trigger refresh loop if /auth/refresh itself returns 401", async () => {
    setTokens("access_token", "refresh_token");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Refresh token invalid" }), { status: 401 })
    );
    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: "refresh_token" }),
    });

    expect(res.status).toBe(401);
    // Should call fetch only once for /auth/refresh without retrying
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(getAccessToken()).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  // 6. Only one retry occurs
  it("6. enforces maximum ONE retry per original request", async () => {
    setTokens("access_1", "refresh_1");

    const fetchMock = vi.fn()
      // Original request -> 401
      .mockResolvedValueOnce(new Response("401", { status: 401 }))
      // Refresh request -> 200 with new tokens
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ access_token: "access_2", refresh_token: "refresh_2", token_type: "bearer" }),
          { status: 200 }
        )
      )
      // Retry request STILL -> 401
      .mockResolvedValueOnce(new Response("401", { status: 401 }));

    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/jobs");
    expect(res.status).toBe(401);

    // Total calls: Original (1) + Refresh (1) + Retry (1) = 3 calls total
    expect(fetchMock).toHaveBeenCalledTimes(3);
    // State cleared & redirected after failed retry
    expect(window.location.href).toBe("/login");
  });

  // 7. Multiple simultaneous 401 responses share one refresh request (Single-flight)
  it("7. coalesces concurrent 401 responses into a single refresh request", async () => {
    setTokens("old_access", "valid_refresh");

    let refreshCallCount = 0;

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/auth/refresh")) {
        refreshCallCount++;
        return Promise.resolve(
          new Response(
            JSON.stringify({
              access_token: "shared_new_access_token",
              refresh_token: "shared_new_refresh_token",
              token_type: "bearer",
            }),
            { status: 200 }
          )
        );
      }

      // Initial calls return 401 if header has old_access, else 200
      const reqHeaders = fetchMock.mock.calls[fetchMock.mock.calls.length - 1]?.[1]?.headers as Headers;
      const authHeader = reqHeaders?.get("Authorization");

      if (authHeader === "Bearer old_access") {
        return Promise.resolve(new Response("401", { status: 401 }));
      }
      return Promise.resolve(new Response(JSON.stringify({ success: true }), { status: 200 }));
    });

    global.fetch = fetchMock;

    // Fire 5 concurrent API requests simultaneously
    const requests = [
      apiFetch("/api/v1/req1"),
      apiFetch("/api/v1/req2"),
      apiFetch("/api/v1/req3"),
      apiFetch("/api/v1/req4"),
      apiFetch("/api/v1/req5"),
    ];

    const results = await Promise.all(requests);

    results.forEach((res) => expect(res.status).toBe(200));

    // Exactly 1 refresh request sent for all 5 concurrent calls!
    expect(refreshCallCount).toBe(1);
    expect(getAccessToken()).toBe("shared_new_access_token");
  });

  // 8. HTTP 403 does not trigger refresh
  it("8. returns HTTP 403 Forbidden without attempting token refresh", async () => {
    setTokens("access_token", "refresh_token");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Forbidden access" }), { status: 403 })
    );
    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/admin/dashboard");
    expect(res.status).toBe(403);

    // Call count = 1 (no refresh attempt)
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(getAccessToken()).toBe("access_token");
  });

  // 10. Logout clears authentication state
  it("10. logoutAndRedirect clears all tokens and org ID", () => {
    setTokens("access", "refresh");
    setOrgId("org123");

    logoutAndRedirect("/login");

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(getOrgId()).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  // 11. Requisition reporting API helpers
  it("11. fetchRequisitionReport calls GET /api/v1/requisitions/{id}/report", async () => {
    setTokens("valid_token", "refresh");
    setOrgId("org_123");

    const mockReport = {
      requisition_id: "job-123",
      title: "Backend Engineer",
      total_applications: 5,
    };

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(mockReport), { status: 200 })
    );
    global.fetch = fetchMock;

    const { fetchRequisitionReport } = await import("./api");
    const data = await fetchRequisitionReport("job-123");

    expect(data).toEqual(mockReport);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/requisitions/job-123/report");
  });
});
