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
  const { user, activeRole, isLoading, isAuthenticated, logout } = useAuth();
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

    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-white p-6">
        <div className="glass-panel p-8 rounded-3xl max-w-lg w-full border border-rose-500/30 bg-rose-950/20 text-center">
          <div className="w-12 h-12 rounded-full bg-rose-500/20 border border-rose-500/50 flex items-center justify-center mx-auto mb-4 text-rose-400 font-bold text-xl">
            403
          </div>
          <span className="text-xs font-mono text-rose-400 uppercase tracking-widest block mb-2">
            Portal Isolation Guard
          </span>
          <h2 className="text-2xl font-black text-white tracking-tight mb-3">
            Unauthorized Portal Access
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed mb-6">
            Your account <span className="font-mono text-sky-400">{user?.email}</span> has assigned role{" "}
            <span className="font-mono font-bold text-amber-400">{activeRole || "UNKNOWN"}</span>. You do not have permission to access the{" "}
            <span className="font-mono text-rose-400 capitalize">{primaryAllowedPortal}</span> portal.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => router.push(homeUrl)}
              className="py-3 px-5 text-sm font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 rounded-xl transition-colors"
            >
              Go to Your Portal ({homeUrl.split("/")[1]})
            </button>
            <button
              onClick={() => logout(`/login?portal=${primaryAllowedPortal}`)}
              className="py-3 px-5 text-sm font-semibold glass-panel-hover text-slate-300 border border-slate-700 rounded-xl"
            >
              Switch Account
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
