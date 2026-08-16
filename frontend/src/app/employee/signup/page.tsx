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
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await registerEmployee(email, password, firstName, lastName, companyName || undefined);
      await loginUser(email, password);
      await refetchProfile();
      router.push("/recruiter/dashboard");
    } catch (err: any) {
      setError(err.message || "Employee registration failed.");
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
          Employee &amp; Employer Account Registration
        </span>
      </div>

      {/* Card */}
      <div className="glass-panel p-8 rounded-3xl max-w-md w-full border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="mb-6">
          <h1 className="text-2xl font-black text-white tracking-tight">Create your account</h1>
          <p className="text-xs text-slate-400 mt-1">Build your team and hire great talent.</p>
        </div>

        {error && (
          <div className="p-4 mb-6 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
                First name
              </label>
              <input
                type="text"
                required
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Alex"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
                Last name
              </label>
              <input
                type="text"
                required
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Smith"
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Work email
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
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Company Name <span className="text-slate-500 uppercase">(Optional)</span>
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Acme Corp"
              className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                minLength={8}
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
            <p className="text-[10px] font-mono text-slate-500 mt-1">Minimum 8 characters</p>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 px-4 rounded-xl btn-shimmer font-bold text-white shadow-xl shadow-sky-500/20 text-sm transition-all disabled:opacity-50 mt-2"
          >
            {isSubmitting ? "Creating employee account..." : "Create account"}
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
  );
}
