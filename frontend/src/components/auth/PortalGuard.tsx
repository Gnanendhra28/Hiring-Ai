"use client";

import React, { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "./AuthContext";

export type PortalType = "recruiter" | "candidate" | "admin";

interface PortalGuardProps {
  allowedPortals: PortalType[];
  children: React.ReactNode;
}

export function PortalGuard({ allowedPortals, children }: PortalGuardProps) {
  const { user, activeRole, isLoading, isAuthenticated, savedAccounts, switchAccount, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const primaryAllowedPortal = allowedPortals[0] || "recruiter";
  const isAuthRoute = Boolean(pathname && (pathname.includes("/login") || pathname.includes("/signup")));

  useEffect(() => {
    if (!isAuthRoute && !isLoading && !isAuthenticated) {
      const loginUrl = `/login?portal=${primaryAllowedPortal}&redirect=${encodeURIComponent(pathname)}`;
      router.push(loginUrl);
    }
  }, [isAuthRoute, isLoading, isAuthenticated, primaryAllowedPortal, pathname, router]);

  if (isAuthRoute) {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white">
        <div className="w-12 h-12 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin mb-4" />
        <p className="text-sm font-mono text-slate-400">Verifying Portal Security Context...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white p-4">
        <div className="glass-panel p-8 rounded-2xl max-w-md w-full border border-slate-800 text-center">
          <h2 className="text-xl font-bold mb-2">Authentication Required</h2>
          <p className="text-sm text-slate-400 mb-6">
            Please log in to access the {primaryAllowedPortal.toUpperCase()} portal.
          </p>
          <a
            href={`/login?portal=${primaryAllowedPortal}&redirect=${encodeURIComponent(pathname)}`}
            className="inline-block w-full py-3 px-4 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-xl transition-colors text-center"
          >
            Go to Login
          </a>
        </div>
      </div>
    );
  }

  // Check portal permissions
  const isPlatformAdmin = user?.is_platform_admin || activeRole === "PLATFORM_ADMIN";

  let isAuthorized = false;

  if (isPlatformAdmin) {
    // Platform admin can access admin and recruiter portals
    if (allowedPortals.includes("admin") || allowedPortals.includes("recruiter")) {
      isAuthorized = true;
    }
  } else if (activeRole === "RECRUITER" || activeRole === "ORGANIZATION_ADMIN") {
    if (allowedPortals.includes("recruiter")) {
      isAuthorized = true;
    }
  } else if (activeRole === "CANDIDATE") {
    if (allowedPortals.includes("candidate")) {
      isAuthorized = true;
    }
  }

  if (!isAuthorized) {
    let homeUrl = "/login";
    if (isPlatformAdmin) homeUrl = "/admin/dashboard";
    else if (activeRole === "RECRUITER" || activeRole === "ORGANIZATION_ADMIN") homeUrl = "/recruiter/dashboard";
    else if (activeRole === "CANDIDATE") homeUrl = "/candidate/dashboard";

    const matchingSavedAccounts = (savedAccounts || []).filter((a) => {
      if (primaryAllowedPortal === "admin") return a.role === "PLATFORM_ADMIN";
      if (primaryAllowedPortal === "recruiter") return a.role === "RECRUITER" || a.role === "ORGANIZATION_ADMIN";
      if (primaryAllowedPortal === "candidate") return a.role === "CANDIDATE";
      return false;
    });

    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white p-6">
        <div className="glass-panel p-8 rounded-3xl max-w-lg w-full border border-rose-500/30 bg-rose-950/20 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-rose-500/20 border border-rose-500/50 flex items-center justify-center mx-auto text-rose-400 font-bold text-xl">
            403
          </div>
          <span className="text-xs font-mono text-rose-400 uppercase tracking-widest block">
            Portal Isolation Guard
          </span>
          <h2 className="text-2xl font-black text-white tracking-tight">
            Unauthorized Portal Access
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Your current active account <span className="font-mono text-sky-400">{user?.email}</span> has assigned role{" "}
            <span className="font-mono font-bold text-amber-400">{activeRole || "UNKNOWN"}</span>.
          </p>

          {matchingSavedAccounts.length > 0 && (
            <div className="p-3 rounded-2xl bg-slate-900/90 border border-slate-800 text-left space-y-2">
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                Available Accounts with Access:
              </span>
              {matchingSavedAccounts.map((acc) => (
                <button
                  key={acc.email}
                  onClick={() => switchAccount(acc.email)}
                  className="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-800/80 hover:bg-sky-500 hover:text-slate-950 transition-all group"
                >
                  <div className="overflow-hidden mr-2">
                    <p className="text-xs font-bold text-white group-hover:text-slate-950 truncate">{acc.fullName || acc.email}</p>
                    <p className="text-[10px] text-slate-400 group-hover:text-slate-800 font-mono truncate">{acc.email}</p>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-1 rounded bg-sky-500/20 text-sky-300 group-hover:bg-slate-950 group-hover:text-white shrink-0">
                    Switch & Continue →
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <button
              onClick={() => router.push(homeUrl)}
              className="py-3 px-5 text-xs font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 rounded-xl transition-colors"
            >
              Return to Your Portal ({homeUrl.split("/")[1]})
            </button>
            <button
              onClick={() => logout(`/login?portal=${primaryAllowedPortal}`)}
              className="py-3 px-5 text-xs font-semibold glass-panel hover:bg-slate-800 text-slate-300 border border-slate-700 rounded-xl"
            >
              Sign In with Another Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
