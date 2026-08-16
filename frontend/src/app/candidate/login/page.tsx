"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";

export default function CandidateLoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [forgotNotice, setForgotNotice] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setForgotNotice(false);

    if (!email || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setIsSubmitting(true);

    try {
      await login(email, password);
      router.push("/candidate/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid email address or password. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans selection:bg-sky-500 selection:text-white relative overflow-hidden">
      {/* ------------------------------------------------ LEFT SIDE: MARKETING & POSITIONING PANEL ------------------------------------------------ */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-slate-900/60 border-r border-slate-800 p-12 flex-col justify-between overflow-hidden">
        {/* Ambient background glow & grid */}
        <div className="absolute inset-0 bg-hero-glow pointer-events-none opacity-40 z-0" />
        <div className="absolute inset-0 bg-grid-pattern opacity-15 pointer-events-none z-0" />

        {/* Brand Header */}
        <div className="relative z-10">
          <Link href="/" className="inline-flex items-center space-x-3 mb-6 group">
            <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-lg shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
              AH
            </div>
            <span className="text-2xl font-black text-white tracking-tight">
              AuraHire <span className="text-gradient-cyan">AI Enterprise</span>
            </span>
          </Link>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
            <span>CANDIDATE PORTAL ACCESS</span>
          </div>
        </div>

        {/* Value Proposition */}
        <div className="relative z-10 max-w-lg my-auto space-y-6">
          <h1 className="text-4xl xl:text-5xl font-black text-white tracking-tight leading-tight">
            Hire with AI. <br />
            <span className="text-gradient-cyan">Decide with evidence.</span>
          </h1>
          <p className="text-slate-300 text-base leading-relaxed">
            Explainable candidate matching and evidence-backed hiring intelligence built around human decision authority.
          </p>

          {/* Governance Badge */}
          <div className="p-4 rounded-2xl glass-panel border border-emerald-500/30 flex items-center space-x-3 bg-emerald-950/20">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-sm">
              ✓
            </div>
            <div>
              <div className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">AI ASSISTS. RECRUITER DECIDES.</div>
              <div className="text-xs text-slate-300">Deterministic scoring engine with zero autonomous decision paths.</div>
            </div>
          </div>

          {/* Candidate Feature Highlights */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-3 text-xs font-medium text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Intelligent opportunity alignment via multi-factor vector analysis</span>
            </div>
            <div className="flex items-center space-x-3 text-xs font-medium text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Transparent, evidence-backed skill verification metrics</span>
            </div>
            <div className="flex items-center space-x-3 text-xs font-medium text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Full visibility into your application status and interview workflow</span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 text-xs text-slate-500 font-mono flex items-center justify-between">
          <span>© 2026 AuraHire AI Enterprise</span>
          <span>v1.0.0 • Secured by RLS &amp; JWT</span>
        </div>
      </div>

      {/* ------------------------------------------------ RIGHT SIDE: AUTHENTICATION CARD ------------------------------------------------ */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 relative">
        <div className="glass-panel p-8 md:p-10 rounded-3xl max-w-md w-full border border-slate-800 shadow-2xl relative z-10">
          {/* Mobile Header */}
          <div className="lg:hidden text-center mb-8">
            <Link href="/" className="inline-flex items-center space-x-3 mb-2">
              <div className="w-9 h-9 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-base">
                AH
              </div>
              <span className="text-xl font-black text-white tracking-tight">
                AuraHire <span className="text-gradient-cyan">AI</span>
              </span>
            </Link>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-black text-white tracking-tight">Welcome back</h2>
            <p className="text-xs text-slate-400 mt-1">Sign in to continue your job search.</p>
          </div>

          {error && (
            <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-start space-x-2">
              <span className="text-rose-400 font-bold">!</span>
              <span>{error}</span>
            </div>
          )}

          {forgotNotice && (
            <div className="p-4 mb-6 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-start space-x-2">
              <span className="font-bold">ℹ</span>
              <span>Password reset isn&apos;t configured yet. Please contact your administrator.</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
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
                  onClick={() => setForgotNotice(true)}
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
                  placeholder="••••••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono pr-12 transition-all"
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
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <span>Log in</span>
              )}
            </button>
          </form>

          {/* OAuth Section */}
          <div className="my-6 flex items-center justify-center space-x-3">
            <div className="h-px bg-slate-800 flex-1" />
            <span className="text-[10px] font-mono uppercase text-slate-500 px-2">
              Or continue with
            </span>
            <div className="h-px bg-slate-800 flex-1" />
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <button
              type="button"
              disabled
              className="py-2.5 px-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-500 text-xs font-semibold flex items-center justify-center space-x-2 cursor-not-allowed opacity-60"
            >
              <span>Google</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">Coming soon</span>
            </button>

            <button
              type="button"
              disabled
              className="py-2.5 px-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-500 text-xs font-semibold flex items-center justify-center space-x-2 cursor-not-allowed opacity-60"
            >
              <span>LinkedIn</span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">Coming soon</span>
            </button>
          </div>

          {/* Footer Link */}
          <div className="text-center pt-4 border-t border-slate-800 text-xs text-slate-400">
            Don&apos;t have an account?{" "}
            <Link href="/candidate/signup" className="text-sky-400 font-bold hover:underline">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
