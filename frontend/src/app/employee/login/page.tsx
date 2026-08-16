"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";

export default function EmployeeLoginPage() {
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
    setIsSubmitting(true);

    try {
      await login(email, password);
      router.push("/recruiter/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid work email address or password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 text-white">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <Link href="/" className="inline-flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-lg shadow-lg shadow-sky-500/20">
            AH
          </div>
          <span className="text-2xl font-black text-white tracking-tight">
            AuraHire <span className="text-gradient-cyan">AI Enterprise</span>
          </span>
        </Link>
        <span className="block text-xs font-mono uppercase tracking-widest text-indigo-400">
          Employee &amp; Recruiter Portal
        </span>
      </div>

      {/* Card */}
      <div className="glass-panel p-8 rounded-3xl max-w-md w-full border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="mb-6">
          <h1 className="text-2xl font-black text-white tracking-tight">Welcome back</h1>
          <p className="text-xs text-slate-400 mt-1">Sign in to manage your hiring workflow.</p>
        </div>

        {error && (
          <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            {error}
          </div>
        )}

        {forgotNotice && (
          <div className="p-4 mb-6 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
            Password reset requires administrator verification. Please contact system administrator.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Work Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-mono uppercase text-slate-400">
                Password
              </label>
              <button
                type="button"
                onClick={() => setForgotNotice(true)}
                className="text-xs font-mono text-sky-400 hover:underline"
              >
                Forgot?
              </button>
            </div>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 text-xs"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 px-4 rounded-xl btn-shimmer font-bold text-white shadow-xl shadow-sky-500/20 text-sm transition-all disabled:opacity-50 mt-2"
          >
            {isSubmitting ? "Signing in..." : "Log in"}
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
            title="OAuth integration not configured"
            className="py-2.5 px-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-500 text-xs font-semibold flex items-center justify-center space-x-2 cursor-not-allowed opacity-60"
          >
            <span>Google</span>
            <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-slate-500">Disabled</span>
          </button>

          <button
            type="button"
            disabled
            title="OAuth integration not configured"
            className="py-2.5 px-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-500 text-xs font-semibold flex items-center justify-center space-x-2 cursor-not-allowed opacity-60"
          >
            <span>LinkedIn</span>
            <span className="text-[9px] font-mono px-1 rounded bg-slate-800 text-slate-500">Disabled</span>
          </button>
        </div>

        {/* Footer Link */}
        <div className="text-center pt-4 border-t border-slate-800 text-xs text-slate-400">
          Don&apos;t have an account?{" "}
          <Link href="/employee/signup" className="text-sky-400 font-bold hover:underline">
            Create employee account
          </Link>
        </div>
      </div>
    </div>
  );
}
