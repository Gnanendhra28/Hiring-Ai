"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";

function LoginRedirectContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { isAuthenticated, activeRole, isLoading } = useAuth();

  const portalParam = searchParams.get("portal");

  useEffect(() => {
    if (isLoading) return;

    if (isAuthenticated && activeRole) {
      if (activeRole === "CANDIDATE") {
        router.replace("/candidate/dashboard");
      } else {
        router.replace("/recruiter/dashboard");
      }
      return;
    }

    if (portalParam === "employee" || portalParam === "recruiter") {
      router.replace("/employee/login");
    } else {
      router.replace("/candidate/login");
    }
  }, [isLoading, isAuthenticated, activeRole, portalParam, router]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 text-white">
      <div className="text-center space-y-3">
        <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-lg mx-auto shadow-lg shadow-sky-500/20">
          AH
        </div>
        <p className="text-sm font-mono text-slate-400">Redirecting to secure portal login...</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 text-white p-12 text-center font-mono">Redirecting...</div>}>
      <LoginRedirectContent />
    </Suspense>
  );
}
