"use client";

import React from "react";
import Link from "next/link";

export default function SignupChoicePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-sky-500 selection:text-white relative overflow-hidden font-sans">
      {/* Ambient background glow & grid */}
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

      {/* Main Choice Container */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-2xl text-center">
          <h1 className="text-3xl md:text-4xl font-black text-white tracking-tight mb-2">
            Create your account
          </h1>
          <p className="text-sm text-slate-400 max-w-md mx-auto mb-10">
            Select your account type to get started with AuraHire AI Enterprise.
          </p>

          <div className="grid md:grid-cols-2 gap-6 text-left">
            {/* Candidate Card */}
            <Link
              href="/candidate/signup"
              className="glass-panel p-8 rounded-3xl border border-slate-800 hover:border-sky-500/50 hover:bg-slate-900/90 transition-all group relative overflow-hidden flex flex-col justify-between"
            >
              <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center mb-6 text-sky-400 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-sky-400 tracking-widest block mb-1">
                  Candidate Portal
                </span>
                <h2 className="text-xl font-bold text-white group-hover:text-sky-300 transition-colors mb-2">
                  Job Seeker / Candidate
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed mb-6">
                  Build your verified candidate profile, track applications, and access evidence-backed AI job recommendations.
                </p>
              </div>

              <div className="text-xs font-bold text-sky-400 flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                <span>Continue as Candidate</span>
                <span>→</span>
              </div>
            </Link>

            {/* Employee / Recruiter Card */}
            <Link
              href="/employee/signup"
              className="glass-panel p-8 rounded-3xl border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900/90 transition-all group relative overflow-hidden flex flex-col justify-between"
            >
              <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center mb-6 text-indigo-400 group-hover:scale-110 transition-transform">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5m0 0h5m-5 0V11m0 0h-2m2 0h2" />
                </svg>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase font-bold text-indigo-400 tracking-widest block mb-1">
                  Enterprise Portal
                </span>
                <h2 className="text-xl font-bold text-white group-hover:text-indigo-300 transition-colors mb-2">
                  Employee / Recruiter
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed mb-6">
                  Post requisitions, execute deterministic candidate matching, and manage pipeline operations.
                </p>
              </div>

              <div className="text-xs font-bold text-indigo-400 flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
                <span>Continue as Recruiter</span>
                <span>→</span>
              </div>
            </Link>
          </div>

          <div className="mt-10 text-xs text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="text-sky-400 font-bold hover:underline">
              Log in
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-6 text-center text-xs text-slate-500 font-mono border-t border-slate-900/60">
        © 2026 AuraHire AI Enterprise • Account Selection
      </footer>
    </div>
  );
}
