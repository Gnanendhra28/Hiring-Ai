"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth, RoleType } from "@/components/auth/AuthContext";

function LoginFormContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { login, isAuthenticated, activeRole, isLoading } = useAuth();

  const portalParam = searchParams.get("portal") || "recruiter";
  const redirectParam = searchParams.get("redirect") || "";

  const [activeTab, setActiveTab] = useState<"recruiter" | "candidate" | "admin">(
    portalParam === "admin" ? "admin" : portalParam === "candidate" ? "candidate" : "recruiter"
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated && activeRole) {
      if (redirectParam) {
        router.push(redirectParam);
        return;
      }
      if (activeRole === "PLATFORM_ADMIN") {
        router.push(activeTab === "recruiter" ? "/recruiter/dashboard" : "/admin/dashboard");
      } else if (activeRole === "RECRUITER" || activeRole === "ORGANIZATION_ADMIN") {
        router.push("/recruiter/dashboard");
      } else if (activeRole === "CANDIDATE") {
        router.push("/candidate/dashboard");
      }
    }
  }, [isLoading, isAuthenticated, activeRole, redirectParam, activeTab, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      // AuthContext will trigger loadProfile & redirect effect
    } catch (err: any) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoCredentials = (role: "recruiter" | "candidate" | "admin") => {
    if (role === "recruiter") {
      setEmail("recruiter@acme.com");
      setPassword("RecruiterPassword123!");
      setActiveTab("recruiter");
    } else if (role === "candidate") {
      setEmail("candidate@example.com");
      setPassword("CandidatePassword123!");
      setActiveTab("candidate");
    } else if (role === "admin") {
      setEmail("admin@hiringai.com");
      setPassword("AdminPassword123!");
      setActiveTab("admin");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 text-white">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <a href="/" className="inline-flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-lg shadow-lg shadow-sky-500/20">
            AH
          </div>
          <span className="text-2xl font-black text-white tracking-tight">
            AuraHire <span className="text-gradient-cyan">AI Enterprise</span>
          </span>
        </a>
        <h1 className="text-xl font-bold text-slate-200">Enterprise Portal Authentication</h1>
        <p className="text-xs text-slate-400 mt-1 font-mono">Role-Based Isolated Entry Point</p>
      </div>

      {/* Auth Card */}
      <div className="glass-panel p-8 rounded-3xl max-w-md w-full border border-slate-800 shadow-2xl relative overflow-hidden">
        {/* Portal Tabs */}
        <div className="grid grid-cols-3 gap-1 p-1 bg-slate-900/90 rounded-xl mb-6 border border-slate-800 text-xs font-semibold text-center">
          <button
            type="button"
            onClick={() => setActiveTab("recruiter")}
            className={`py-2 rounded-lg transition-all ${
              activeTab === "recruiter" ? "bg-sky-500 text-slate-950 font-bold shadow-md" : "text-slate-400 hover:text-white"
            }`}
          >
            Recruiter
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("candidate")}
            className={`py-2 rounded-lg transition-all ${
              activeTab === "candidate" ? "bg-indigo-500 text-slate-950 font-bold shadow-md" : "text-slate-400 hover:text-white"
            }`}
          >
            Candidate
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("admin")}
            className={`py-2 rounded-lg transition-all ${
              activeTab === "admin" ? "bg-purple-500 text-slate-950 font-bold shadow-md" : "text-slate-400 hover:text-white"
            }`}
          >
            Admin
          </button>
        </div>

        {error && (
          <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={
                activeTab === "recruiter"
                  ? "recruiter@acme.com"
                  : activeTab === "candidate"
                  ? "candidate@example.com"
                  : "admin@hiringai.com"
              }
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 px-4 rounded-xl btn-shimmer font-bold text-white shadow-xl shadow-sky-500/20 text-sm transition-all disabled:opacity-50 mt-2"
          >
            {isSubmitting
              ? "Authenticating Identity..."
              : `Sign In to ${activeTab.toUpperCase()} Portal →`}
          </button>
        </form>

        {/* Quick Demo Pre-fill Links */}
        <div className="mt-8 pt-6 border-t border-slate-800">
          <p className="text-[11px] font-mono text-slate-400 text-center mb-3">
            TEST / DEMO IDENTITY PRE-FILLS
          </p>
          <div className="grid grid-cols-3 gap-2 text-[10px] font-mono text-center">
            <button
              onClick={() => fillDemoCredentials("recruiter")}
              className="p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-sky-400 transition-colors"
            >
              Recruiter Demo
            </button>
            <button
              onClick={() => fillDemoCredentials("candidate")}
              className="p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-indigo-400 transition-colors"
            >
              Candidate Demo
            </button>
            <button
              onClick={() => fillDemoCredentials("admin")}
              className="p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-purple-400 transition-colors"
            >
              Admin Demo
            </button>
          </div>
        </div>
      </div>

      <div className="mt-8 text-center text-xs text-slate-500 font-mono">
        PostgreSQL RLS &bull; JWT Bearer &bull; HttpOnly Refresh &bull; Strict Role Isolation
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 text-white p-12 text-center">Loading Login Portal...</div>}>
      <LoginFormContent />
    </Suspense>
  );
}
