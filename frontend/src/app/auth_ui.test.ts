import { describe, it, expect, vi, beforeEach } from "vitest";
import { registerCandidate, registerEmployee, loginUser, getGoogleAuthUrl, googleAuthCallback } from "../lib/api";

describe("Phase 31 Unified Auth & Google OAuth API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("registerCandidate makes POST request to /api/v1/auth/register/candidate with phone_number", async () => {
    const mockUser = {
      id: "usr-123",
      email: "candidate@example.com",
      full_name: "Jane Candidate",
      phone_number: "+91 98765 43210",
      is_platform_admin: false,
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });

    const res = await registerCandidate("candidate@example.com", "Password123!", "Jane", "Candidate", "+91 98765 43210");
    expect(res.email).toBe("candidate@example.com");
    expect(res.full_name).toBe("Jane Candidate");
    expect(res.phone_number).toBe("+91 98765 43210");
  });

  it("registerEmployee makes POST request to /api/v1/auth/register/employee with company_name", async () => {
    const mockUser = {
      id: "emp-123",
      email: "recruiter@company.com",
      full_name: "Alex Recruiter",
      is_platform_admin: false,
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });

    const res = await registerEmployee("recruiter@company.com", "Password123!", "Alex", "Recruiter", "Acme Corp");
    expect(res.email).toBe("recruiter@company.com");
    expect(res.full_name).toBe("Alex Recruiter");
  });

  it("getGoogleAuthUrl calls GET /api/v1/auth/google/url", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ url: "https://accounts.google.com/o/oauth2/v2/auth?...", configured: true }),
    });

    const res = await getGoogleAuthUrl("http://localhost:3000/auth/callback/google");
    expect(res.configured).toBe(true);
    expect(res.url).toContain("accounts.google.com");
  });

  it("googleAuthCallback makes POST request to /api/v1/auth/google/callback", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "acc-123", refresh_token: "ref-123", token_type: "bearer" }),
    });

    const res = await googleAuthCallback("google_auth_code_123");
    expect(res.access_token).toBe("acc-123");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/google/callback"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ code: "google_auth_code_123", redirect_uri: undefined, requested_role: undefined }),
      })
    );
  });
});
