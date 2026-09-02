"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getUserProfile } from "@/lib/api";

function GoogleCallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function processCallback() {
      try {
        const profile = await getUserProfile();
        if (!profile || !isMounted) {
          router.replace("/login");
          return;
        }

        const isPlatformAdmin = profile.user.is_platform_admin;
        const isRecruiter = profile.memberships.some(
          (m) => m.role === "RECRUITER" || m.role === "ORGANIZATION_ADMIN"
        );

        if (isPlatformAdmin) {
          router.replace("/admin/dashboard");
        } else if (isRecruiter) {
          router.replace("/recruiter/dashboard");
        } else {
          router.replace("/candidate/dashboard");
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Authentication verification failed.");
        }
      }
    }

    processCallback();
    return () => {
      isMounted = false;
    };
  }, [router]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
        <div className="glass-panel p-8 rounded-3xl border border-rose-500/30 bg-rose-950/20 max-w-md w-full text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-rose-500/20 border border-rose-500/50 flex items-center justify-center mx-auto text-rose-400 font-bold text-xl">
            !
          </div>
          <h1 className="text-xl font-bold text-white">Google Authentication Failed</h1>
          <p className="text-xs text-rose-300 font-mono leading-relaxed">{error}</p>
          <a
            href="/login"
            className="inline-block py-3 px-6 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs rounded-xl transition-colors"
          >
            Return to Login
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-4">
        <div className="w-12 h-12 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin mx-auto" />
        <h1 className="text-lg font-bold">Verifying Google Identity...</h1>
        <p className="text-xs font-mono text-slate-400">Authenticating with Google OAuth 2.0 and linking security profile...</p>
      </div>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 text-white p-12 text-center font-mono">Authenticating...</div>}>
      <GoogleCallbackContent />
    </Suspense>
  );
}
