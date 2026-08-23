"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerEmployee, loginUser } from "@/lib/api";
import { useAuth } from "@/components/auth/AuthContext";

export default function EmployeeSignupPage() {
  const router = useRouter();
  const { refetchProfile } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter your password.");
      return;
    }

    if (password.length < 8) {
      setError("Password must contain at least 8 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      await registerEmployee(email, password, firstName, lastName, companyName || undefined);
      await loginUser(email, password);
      await refetchProfile();
      router.push("/recruiter/dashboard");
    } catch (err: any) {
      setError(err.message || "We couldn't create your employee account right now. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex font-sans selection:bg-sky-500 selection:text-white relative overflow-hidden">
      {/* ------------------------------------------------ LEFT SIDE: MARKETING & POSITIONING PANEL ------------------------------------------------ */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-slate-900/60 border-r border-slate-800 p-12 flex-col justify-between overflow-hidden">
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
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
            <span>EMPLOYEE &amp; RECRUITER REGISTRATION</span>
          </div>
        </div>

        {/* Value Proposition */}
        <div className="relative z-10 max-w-lg my-auto space-y-6">
          <h1 className="text-4xl xl:text-5xl font-black text-white tracking-tight leading-tight">
            Build your team. <br />
            <span className="text-gradient-cyan">Hire great talent.</span>
          </h1>
          <p className="text-slate-300 text-base leading-relaxed">
            Create an enterprise employee account to manage job requisitions, evaluate candidate evidence, and drive decision workflows.
          </p>

          {/* Governance Badge */}
          <div className="p-4 rounded-2xl glass-panel border border-emerald-500/30 flex items-center space-x-3 bg-emerald-950/20">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-sm">
              ✓
            </div>
            <div>
              <div className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">ENTERPRISE TENANT ISOLATION</div>
              <div className="text-xs text-slate-300">Automatic organization provisioning with PostgreSQL Row-Level Security.</div>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-3 text-xs font-medium text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Server-enforced recruiter role assignment resistant to tampering</span>
            </div>
            <div className="flex items-center space-x-3 text-xs font-medium text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
              <span>Requisition intelligence and 4-factor candidate match scoring</span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 text-xs text-slate-500 font-mono flex items-center justify-between">
          <span>© 2026 AuraHire AI Enterprise</span>
          <span>v1.0.0 • Secured by RLS &amp; JWT</span>
        </div>
      </div>

      {/* ------------------------------------------------ RIGHT SIDE: REGISTRATION CARD ------------------------------------------------ */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12 relative">
        <div className="glass-panel p-8 md:p-10 rounded-3xl max-w-md w-full border border-slate-800 shadow-2xl relative z-10">
          {/* Mobile Header */}
          <div className="lg:hidden text-center mb-8">
            <Link href="/" className="inline-flex items-center space-x-3 mb-2">
              <div className="w-9 h-9 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-base">
                AH
              </div>
              <span className="text-xl font-black text-white tracking-tight">
                AuraHire <span className="text-gradient-cyan">AI Enterprise</span>
              </span>
            </Link>
          </div>

          <div className="mb-6">
            <h2 className="text-2xl font-black text-white tracking-tight">Create your account</h2>
            <p className="text-xs text-slate-400 mt-1">Build your team and hire great talent.</p>
          </div>

          {error && (
            <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold flex items-start space-x-2">
              <span className="text-rose-400 font-bold">!</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="emp-first-name-input" className="block text-xs font-mono uppercase text-slate-400 mb-1">
                  First name
                </label>
                <input
                  id="emp-first-name-input"
                  name="firstName"
                  autoComplete="given-name"
                  type="text"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Alex"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono transition-all"
                />
              </div>
              <div>
                <label htmlFor="emp-last-name-input" className="block text-xs font-mono uppercase text-slate-400 mb-1">
                  Last name
                </label>
                <input
                  id="emp-last-name-input"
                  name="lastName"
                  autoComplete="family-name"
                  type="text"
                  required
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Smith"
                  className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono transition-all"
                />
              </div>
            </div>

            <div>
              <label htmlFor="emp-work-email-input" className="block text-xs font-mono uppercase text-slate-400 mb-1">
                Work email
              </label>
              <input
                id="emp-work-email-input"
                name="email"
                autoComplete="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono transition-all"
              />
            </div>

            <div>
              <label htmlFor="emp-company-name-input" className="block text-xs font-mono uppercase text-slate-400 mb-1">
                Company name <span className="text-slate-500 uppercase">(Optional)</span>
              </label>
              <input
                id="emp-company-name-input"
                name="companyName"
                autoComplete="organization"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Acme Corp"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono transition-all"
              />
            </div>

            <div>
              <label htmlFor="emp-password-input" className="block text-xs font-mono uppercase text-slate-400 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="emp-password-input"
                  name="password"
                  autoComplete="new-password"
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
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

            <div>
              <label htmlFor="emp-confirm-password-input" className="block text-xs font-mono uppercase text-slate-400 mb-1">
                Confirm Password
              </label>
              <input
                id="emp-confirm-password-input"
                name="confirmPassword"
                autoComplete="new-password"
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 text-sm font-mono transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 px-4 rounded-xl btn-shimmer font-bold text-white shadow-xl shadow-sky-500/20 text-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 mt-4"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Creating employee account...</span>
                </>
              ) : (
                <span>Create account</span>
              )}
            </button>
          </form>

          {/* Footer Link */}
          <div className="text-center pt-6 mt-6 border-t border-slate-800 text-xs text-slate-400">
            Already have an account?{" "}
            <Link href="/employee/login" className="text-sky-400 font-bold hover:underline">
              Log in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
