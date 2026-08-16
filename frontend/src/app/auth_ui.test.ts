import { describe, it, expect, vi, beforeEach } from "vitest";
import { registerCandidate, registerEmployee, loginUser } from "../lib/api";

describe("Phase 28 Candidate & Employee Auth API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("registerCandidate makes POST request to /api/v1/auth/register/candidate with first_name and last_name", async () => {
    const mockUser = {
      id: "usr-123",
      email: "candidate@example.com",
      full_name: "Jane Candidate",
      is_platform_admin: false,
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });

    const res = await registerCandidate("candidate@example.com", "Password123!", "Jane", "Candidate");
    expect(res.email).toBe("candidate@example.com");
    expect(res.full_name).toBe("Jane Candidate");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/register/candidate"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "candidate@example.com",
          password: "Password123!",
          first_name: "Jane",
          last_name: "Candidate",
        }),
      })
    );
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
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/register/employee"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "recruiter@company.com",
          password: "Password123!",
          first_name: "Alex",
          last_name: "Recruiter",
          company_name: "Acme Corp",
        }),
      })
    );
  });
});
