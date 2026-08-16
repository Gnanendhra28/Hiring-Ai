"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";
import { getGoogleAuthUrl, getUserProfile } from "@/lib/api";

export default function UnifiedLoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, user, activeRole } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [googleNotice, setGoogleNotice] = useState<string | null>(null);
  const [forgotNotice, setForgotNotice] = useState<string | null>(null);

  // If user is already authenticated, redirect to appropriate portal
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.is_platform_admin) {
        router.replace("/admin/dashboard");
      } else if (activeRole === "RECRUITER" || activeRole === "ORGANIZATION_ADMIN") {
        router.replace("/recruiter/dashboard");
      } else {
        router.replace("/candidate/dashboard");
      }
    }
  }, [isAuthenticated, user, activeRole, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setGoogleNotice(null);
    setForgotNotice(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      // Retrieve fresh profile to determine server-side role
      const profile = await getUserProfile();
      const isPlatformAdmin = Boolean(profile?.user?.is_platform_admin);
      const isRecruiter = Boolean(
        profile?.memberships?.some(
          (m) => m.role === "RECRUITER" || m.role === "ORGANIZATION_ADMIN"
        )
      );

      if (isPlatformAdmin) {
        router.push("/admin/dashboard");
      } else if (isRecruiter) {
        router.push("/recruiter/dashboard");
      } else {
        router.push("/candidate/dashboard");
      }
    } catch (err: any) {
      setError(err.message || "Invalid email address or password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError(null);
    setGoogleNotice(null);
    try {
      const res = await getGoogleAuthUrl();
      if (res.configured && res.url) {
        window.location.href = res.url;
      } else {
        setGoogleNotice("Google OAuth: Configuration Required. Set GOOGLE_CLIENT_ID in server environment to enable live Google Sign-In.");
      }
    } catch (err: any) {
      setGoogleNotice("Google OAuth endpoint unavailable. Check backend connection.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white relative overflow-hidden font-sans">
      {/* Background Ambient Glow & Grid */}
      <div className="fixed inset-0 bg-hero-glow pointer-events-none opacity-30 z-0" />
      <div className="fixed inset-0 bg-grid-pattern opacity-10 pointer-events-none z-0" />

      {/* Header */}
      <header className="relative z-10 max-w-7xl mx-auto px-6 py-6 w-full flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="text-lg font-extrabold tracking-tight text-white">
            AuraHire<span className="text-gradient-cyan">AI</span>
            <span className="text-[9px] font-semibold uppercase px-2 py-0.5 ml-2 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Enterprise
            </span>
          </span>
        </Link>
      </header>

      {/* Main Login Card */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md glass-panel p-8 md:p-10 rounded-3xl border border-slate-800 shadow-2xl backdrop-blur-xl">
          <div className="mb-6">
            <h1 className="text-3xl font-black text-white tracking-tight">Welcome back</h1>
            <p className="text-xs text-slate-400 mt-1.5">Sign in to continue to AuraHire.</p>
          </div>

          {error && (
            <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-start space-x-2">
              <span className="text-rose-400 font-bold">!</span>
              <span>{error}</span>
            </div>
          )}

          {googleNotice && (
            <div className="p-4 mb-6 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono leading-relaxed">
              <span className="font-bold text-amber-400 block mb-1">Notice</span>
              {googleNotice}
            </div>
          )}

          {forgotNotice && (
            <div className="p-4 mb-6 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-300 text-xs font-mono leading-relaxed">
              {forgotNotice}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email-input" className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
                Email
              </label>
              <input
                id="email-input"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono transition-all"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password-input" className="text-xs font-mono uppercase text-slate-400">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setForgotNotice("Contact your organization administrator to initiate a secure password reset.")}
                  className="text-xs font-mono text-sky-400 hover:text-sky-300 hover:underline transition-colors"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  id="password-input"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono pr-14 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3.5 text-slate-400 hover:text-white text-xs font-mono"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 px-4 rounded-xl btn-shimmer font-bold text-white shadow-xl shadow-sky-500/20 text-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 mt-2"
            >
              {isSubmitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <span>Log in</span>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center justify-center space-x-3">
            <div className="h-px bg-slate-800 flex-1" />
            <span className="text-[10px] font-mono uppercase text-slate-500 px-2 tracking-wider">
              Or continue with
            </span>
            <div className="h-px bg-slate-800 flex-1" />
          </div>

          {/* Real Google OAuth Button */}
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="w-full py-3 px-4 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/80 text-slate-200 text-xs font-semibold flex items-center justify-center space-x-3 transition-all"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Google</span>
          </button>

          {/* Footer */}
          <div className="text-center pt-6 mt-6 border-t border-slate-800 text-xs text-slate-400">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="text-sky-400 font-bold hover:underline">
              Sign up
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-6 text-center text-xs text-slate-500 font-mono border-t border-slate-900/60">
        © 2026 AuraHire AI Enterprise • Unified Authentication
      </footer>
    </div>
  );
}
