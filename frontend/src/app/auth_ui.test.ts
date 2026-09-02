import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchUserProfile, getCandidateProfile, updateCandidateProfile, setTokens } from "../lib/api";

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

Object.defineProperty(global, "window", {
  value: {
    location: {
      href: "",
      pathname: "/",
    },
    localStorage: localStorageMock,
  },
  writable: true,
});

describe("Firebase Identity & Profile API Client", () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.restoreAllMocks();
  });

  it("fetchUserProfile makes GET request to /api/v1/auth/me", async () => {
    setTokens("mock_token", "mock_token");
    const mockProfile = {
      user: {
        id: "usr-123",
        email: "candidate@example.com",
        full_name: "Jane Candidate",
        is_platform_admin: false,
        is_active: true,
      },
      memberships: [],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockProfile,
    });

    const res = await fetchUserProfile();
    expect(res).not.toBeNull();
    expect(res?.user.email).toBe("candidate@example.com");
    expect(res?.user.full_name).toBe("Jane Candidate");
  });

  it("getCandidateProfile fetches candidate profile metadata", async () => {
    const mockCandidate = {
      id: "cp-123",
      user_id: "usr-123",
      headline: "Senior AI Engineer",
      skills: ["Python", "PyTorch", "Next.js"],
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCandidate,
    });

    const res = await getCandidateProfile();
    expect(res?.headline).toBe("Senior AI Engineer");
    expect(res?.skills).toContain("Python");
  });

  it("updateCandidateProfile sends PUT request to /api/v1/candidate/profile", async () => {
    const updatePayload = { headline: "Staff AI Engineer" };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "cp-123", headline: "Staff AI Engineer" }),
    });

    const res = await updateCandidateProfile(updatePayload);
    expect(res.headline).toBe("Staff AI Engineer");
  });
});
