"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import {
  AuthUser,
  OrgMembership,
  fetchUserProfile,
  loginUser as apiLoginUser,
  logoutAndRedirect,
  getAccessToken,
  clearTokens,
  setOrgId,
  getOrgId,
} from "@/lib/api";

export type RoleType = "PLATFORM_ADMIN" | "ORGANIZATION_ADMIN" | "RECRUITER" | "CANDIDATE";

interface AuthContextType {
  user: AuthUser | null;
  memberships: OrgMembership[];
  activeRole: RoleType | null;
  activeOrgId: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: (redirectUrl?: string) => void;
  refetchProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [memberships, setMemberships] = useState<OrgMembership[]>([]);
  const [activeRole, setActiveRole] = useState<RoleType | null>(null);
  const [activeOrgId, setActiveOrgIdState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setMemberships([]);
      setActiveRole(null);
      setActiveOrgIdState(null);
      setIsLoading(false);
      return;
    }

    try {
      const data = await fetchUserProfile();
      if (data && data.user) {
        setUser(data.user);
        setMemberships(data.memberships || []);

        let role: RoleType = "CANDIDATE";
        if (data.user.is_platform_admin) {
          role = "PLATFORM_ADMIN";
        } else if (data.memberships && data.memberships.length > 0) {
          const storedOrgId = getOrgId();
          const activeMem = data.memberships.find(m => m.organization_id === storedOrgId) || data.memberships[0];
          role = activeMem.role as RoleType;
          setOrgId(activeMem.organization_id);
          setActiveOrgIdState(activeMem.organization_id);
        }
        setActiveRole(role);
      } else {
        setUser(null);
        setMemberships([]);
        setActiveRole(null);
        setActiveOrgIdState(null);
      }
    } catch {
      setUser(null);
      setMemberships([]);
      setActiveRole(null);
      setActiveOrgIdState(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const login = async (email: string, password: string) => {
    await apiLoginUser(email, password);
    await loadProfile();
  };

  const logout = (redirectUrl = "/login") => {
    clearTokens();
    setUser(null);
    setMemberships([]);
    setActiveRole(null);
    setActiveOrgIdState(null);
    logoutAndRedirect(redirectUrl);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        memberships,
        activeRole,
        activeOrgId,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refetchProfile: loadProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
