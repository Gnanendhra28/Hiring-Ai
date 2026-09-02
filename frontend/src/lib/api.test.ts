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

vi.mock("./firebase", () => {
  return {
    firebaseAuth: {
      currentUser: {
        getIdToken: vi.fn().mockResolvedValue("new_firebase_id_token_999"),
      },
    },
  };
});

describe("Frontend API Client & Auth Refresh Interceptor", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.restoreAllMocks();
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

  it("1. includes Bearer token and X-Organization-ID on normal authenticated request", async () => {
    setTokens("test_access_token", "test_refresh_token");
    setOrgId("test_org_123");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true }), { status: 200 })
    );
    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/recruiter/jobs");
    expect(res.status).toBe(200);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/v1/recruiter/jobs");
    const headers = options.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer test_access_token");
    expect(headers.get("X-Organization-ID")).toBe("test_org_123");
  });

  it("2. triggers Firebase token refresh on 401 and retries request", async () => {
    setTokens("old_access_token", "valid_refresh_token");

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Token expired" }), { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ data: "success" }), { status: 200 }));

    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/jobs");
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(2);

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/jobs");
    expect((fetchMock.mock.calls[0][1].headers as Headers).get("Authorization")).toBe("Bearer old_access_token");

    expect(fetchMock.mock.calls[1][0]).toContain("/api/v1/jobs");
    expect((fetchMock.mock.calls[1][1].headers as Headers).get("Authorization")).toBe("Bearer new_firebase_id_token_999");
  });

  it("3. returns HTTP 403 Forbidden without attempting token refresh", async () => {
    setTokens("access_token", "refresh_token");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Forbidden access" }), { status: 403 })
    );
    global.fetch = fetchMock;

    const res = await apiFetch("/api/v1/admin/secrets");
    expect(res.status).toBe(403);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
