"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"scoring" | "verification" | "governance">("scoring");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-sky-500 selection:text-white relative overflow-hidden font-sans">
      {/* Background Ambient Glow & Grid */}
      <div className="absolute inset-0 bg-hero-glow pointer-events-none z-0" />
      <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none z-0" />

      {/* ---------------------------------------------------------------- border-b ---------------------------------------------------------------- */}
      {/* 1. PREMIUM NAVBAR */}
      <nav className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/25">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-white flex items-center gap-2">
                AuraHire<span className="text-gradient-cyan">AI</span>
                <span className="text-[10px] font-semibold tracking-wide uppercase px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  Enterprise
                </span>
              </span>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-300">
            <a href="#capabilities" className="hover:text-sky-400 transition-colors">Capabilities</a>
            <a href="#matching" className="hover:text-sky-400 transition-colors">Deterministic Scoring</a>
            <a href="#workflow" className="hover:text-sky-400 transition-colors">Workflow</a>
            <a href="#governance" className="hover:text-sky-400 transition-colors">AI Governance</a>
            <a href="#security" className="hover:text-sky-400 transition-colors">Security</a>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              href="/recruiter/dashboard"
              className="px-4 py-2 text-xs md:text-sm font-semibold rounded-lg bg-sky-500 hover:bg-sky-400 text-white transition-all shadow-md shadow-sky-500/20 hover:shadow-sky-500/40"
            >
              Recruiter Portal
            </Link>
            <Link
              href="/candidate/dashboard"
              className="px-4 py-2 text-xs md:text-sm font-medium rounded-lg glass-panel hover:bg-slate-800 text-slate-200 border border-slate-700 transition-all"
            >
              Candidate Portal
            </Link>
            <Link
              href="/admin/dashboard"
              className="hidden lg:inline-flex px-3 py-2 text-xs font-mono font-medium rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              Admin
            </Link>
          </div>
        </div>
      </nav>

      {/* ---------------------------------------------------------------- HERO SECTION ---------------------------------------------------------------- */}
      <section className="relative z-10 pt-16 pb-20 md:pt-28 md:pb-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full glass-panel border border-sky-500/30 text-sky-300 text-xs font-semibold uppercase tracking-wider mb-8 animate-pulse-slow">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />
            <span>Enterprise Recruitment Engine • Multi-Tenant & RLS Secured</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl font-black tracking-tight text-white leading-tight mb-6">
            Hire with AI.<br />
            <span className="text-gradient-cyan">Decide with evidence.</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed mb-10">
            Explainable candidate matching, automated evidence verification, and end-to-end recruitment workflow orchestration built on transparent, zero-bias AI governance.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link
              href="/recruiter/dashboard"
              className="w-full sm:w-auto px-8 py-4 text-base font-bold rounded-xl btn-shimmer text-white shadow-xl shadow-sky-500/25 flex items-center justify-center gap-2 group"
            >
              <span>Access Recruiter Portal</span>
              <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>

            <Link
              href="/candidate/dashboard"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-xl glass-panel-hover text-slate-200 border border-slate-700/80 flex items-center justify-center gap-2"
            >
              <span>Candidate Portal</span>
            </Link>

            <Link
              href="/admin/dashboard"
              className="w-full sm:w-auto px-6 py-4 text-base font-mono text-slate-400 hover:text-white border border-transparent hover:border-slate-800 rounded-xl transition-all"
            >
              Platform Admin
            </Link>
          </div>
        </div>

        {/* INTERACTIVE LIVE MOCKUP DEMO CARD */}
        <div className="mt-8 max-w-5xl mx-auto rounded-2xl glass-panel border border-slate-800 p-4 md:p-8 shadow-2xl shadow-sky-950/40 relative">
          <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 mb-6 gap-4">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/80" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs font-mono text-slate-400 ml-2">Job #SENIOR-BACKEND-001 • Live Match Engine</span>
            </div>

            <div className="flex space-x-2 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setActiveTab("scoring")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "scoring" ? "bg-sky-500 text-white shadow" : "text-slate-400 hover:text-white"
                }`}
              >
                4-Factor Match Score
              </button>
              <button
                onClick={() => setActiveTab("verification")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "verification" ? "bg-sky-500 text-white shadow" : "text-slate-400 hover:text-white"
                }`}
              >
                Evidence Verification
              </button>
              <button
                onClick={() => setActiveTab("governance")}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  activeTab === "governance" ? "bg-sky-500 text-white shadow" : "text-slate-400 hover:text-white"
                }`}
              >
                Recruiter Decision Control
              </button>
            </div>
          </div>

          {/* Interactive Tab Content */}
          {activeTab === "scoring" && (
            <div className="grid md:grid-cols-2 gap-6 items-center">
              <div>
                <div className="inline-block px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono mb-3">
                  ELAPSED: 38ms • 100% DETERMINISTIC
                </div>
                <h3 className="text-xl font-bold text-white mb-2">Overall Match Score: 94.2 / 100</h3>
                <p className="text-sm text-slate-300 mb-4">
                  Computed via exact weighted formulas. LLMs do NOT generate score numbers.
                </p>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs font-medium mb-1 text-slate-300">
                      <span>Required Skill Match (35%)</span>
                      <span className="text-sky-400 font-mono">100% (5/5 Matched)</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-sky-400 rounded-full" style={{ width: "100%" }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-medium mb-1 text-slate-300">
                      <span>Preferred Skill Match (25%)</span>
                      <span className="text-sky-400 font-mono">88% (4/5 Matched)</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-sky-400 rounded-full" style={{ width: "88%" }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-medium mb-1 text-slate-300">
                      <span>Experience Range (20%)</span>
                      <span className="text-emerald-400 font-mono">6.5 Yrs (Gate: ≥ 5 Yrs)</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-400 rounded-full" style={{ width: "95%" }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-medium mb-1 text-slate-300">
                      <span>pgvector HNSW Semantic Match (20%)</span>
                      <span className="text-indigo-400 font-mono">92.4% Cosine Similarity</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-400 rounded-full" style={{ width: "92%" }} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Hard Requirement Gate</span>
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    PASSED
                  </span>
                </div>
                <div className="text-xs space-y-2 text-slate-300">
                  <div className="flex items-center justify-between">
                    <span>Python / FastAPI Architecture:</span>
                    <span className="font-mono text-emerald-400">Verified</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>PostgreSQL & pgvector Expertise:</span>
                    <span className="font-mono text-emerald-400">Verified</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Minimum Relevant Experience (≥5.0 Yrs):</span>
                    <span className="font-mono text-emerald-400">6.5 Yrs</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "verification" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">Verified Resume Evidence Quotes</h3>
                <span className="text-xs font-mono text-sky-400">Zero Hallucination Verifier Active</span>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
                  <div className="text-xs font-semibold text-sky-400 mb-1">Requirement: PostgreSQL & HNSW Vector Indexing</div>
                  <blockquote className="text-xs text-slate-300 italic border-l-2 border-sky-500 pl-3 py-1">
                    &quot;Architected high-scale vector search pipeline utilizing PostgreSQL pgvector with HNSW indexes serving 50M embeddings.&quot;
                  </blockquote>
                  <div className="mt-2 text-[10px] font-mono text-emerald-400">✓ Verified Exact Match (Confidence: 99.4%)</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800">
                  <div className="text-xs font-semibold text-sky-400 mb-1">Requirement: Distributed Microservices</div>
                  <blockquote className="text-xs text-slate-300 italic border-l-2 border-indigo-500 pl-3 py-1">
                    &quot;Led backend engineering team in transitioning monolithic services into event-driven FastAPI microservices.&quot;
                  </blockquote>
                  <div className="mt-2 text-[10px] font-mono text-emerald-400">✓ Verified Exact Match (Confidence: 98.1%)</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "governance" && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-indigo-950/50 border border-indigo-500/30 flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                  Human Authority Enforcement
                </div>
                <h4 className="text-lg font-bold text-white">&quot;AI ASSISTS. RECRUITER DECIDES.&quot;</h4>
                <p className="text-xs text-slate-300 max-w-xl">
                  AI recommendations are 100% advisory. The system strictly blocks automated hiring mutations.
                </p>
              </div>
              <div className="flex space-x-2">
                <button className="px-4 py-2 text-xs font-bold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow">
                  ADVANCE
                </button>
                <button className="px-4 py-2 text-xs font-bold rounded-lg bg-rose-600 hover:bg-rose-500 text-white shadow">
                  REJECT
                </button>
                <button className="px-4 py-2 text-xs font-bold rounded-lg bg-amber-600 hover:bg-amber-500 text-white shadow">
                  HOLD
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ---------------------------------------------------------------- CAPABILITY STRIP ---------------------------------------------------------------- */}
      <section id="capabilities" className="border-y border-slate-800 bg-slate-900/40 backdrop-blur-md py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 text-center">
            <div className="p-3">
              <div className="text-base font-extrabold text-white">pgvector HNSW</div>
              <div className="text-xs text-slate-400 mt-0.5">High-Speed Similarity</div>
            </div>
            <div className="p-3">
              <div className="text-base font-extrabold text-white">100% RLS Isolated</div>
              <div className="text-xs text-slate-400 mt-0.5">PostgreSQL Tenant Security</div>
            </div>
            <div className="p-3">
              <div className="text-base font-extrabold text-white">0 AI Mutations</div>
              <div className="text-xs text-slate-400 mt-0.5">Recruiter Decides</div>
            </div>
            <div className="p-3">
              <div className="text-base font-extrabold text-white">HMAC-SHA256</div>
              <div className="text-xs text-slate-400 mt-0.5">Signed Webhooks</div>
            </div>
            <div className="p-3">
              <div className="text-base font-extrabold text-white">CloudWatch / SIEM</div>
              <div className="text-xs text-slate-400 mt-0.5">Audit Log Streaming</div>
            </div>
            <div className="p-3">
              <div className="text-base font-extrabold text-white">P95 &lt; 40ms</div>
              <div className="text-xs text-slate-400 mt-0.5">Enterprise Latency</div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- JOB INTELLIGENCE ---------------------------------------------------------------- */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto relative">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono text-sky-400 uppercase tracking-widest mb-3">Structured Extraction Engine</h2>
          <h3 className="text-3xl md:text-5xl font-black text-white tracking-tight">Job Intelligence & Versioning</h3>
          <p className="text-slate-300 mt-4 text-base md:text-lg">
            Automatically extract structured technical requirements, hard gating constraints, and experience thresholds with full version history and stale intelligence guards.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="glass-panel glass-panel-hover p-8 rounded-2xl border border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mb-6">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h4 className="text-xl font-bold text-white mb-2">Hard & Preferred Skill Split</h4>
            <p className="text-sm text-slate-400 leading-relaxed">
              Separates non-negotiable hard requirements from optional preferred skills to prevent eligible candidates from being wrongly disqualified.
            </p>
          </div>

          <div className="glass-panel glass-panel-hover p-8 rounded-2xl border border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-6">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 className="text-xl font-bold text-white mb-2">Version History (v1, v2)</h4>
            <p className="text-sm text-slate-400 leading-relaxed">
              Modifying job requirements automatically increments the intelligence version, marking stale candidate matches for seamless re-processing.
            </p>
          </div>

          <div className="glass-panel glass-panel-hover p-8 rounded-2xl border border-slate-800">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-6">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 className="text-xl font-bold text-white mb-2">Protected Feature Exclusions</h4>
            <p className="text-sm text-slate-400 leading-relaxed">
              Strict sanitization filters out age, gender, race, location proxies, and protected attributes before candidate scoring begins.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- MATCHING & SCORING ---------------------------------------------------------------- */}
      <section id="matching" className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto bg-slate-900/30 rounded-3xl border border-slate-800/80 my-12">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <span className="text-xs font-mono text-sky-400 uppercase tracking-widest">Explainable AI Architecture</span>
            <h3 className="text-3xl md:text-5xl font-black text-white tracking-tight mt-2 mb-6">
              4-Factor Deterministic Match Scoring
            </h3>
            <p className="text-slate-300 text-base md:text-lg leading-relaxed mb-6">
              Unlike black-box LLMs that produce unexplainable scores, our scoring pipeline is 100% deterministic, reproducible, and verifiable.
            </p>

            <div className="space-y-4">
              <div className="flex items-start space-x-4 p-4 rounded-xl glass-panel">
                <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 font-bold font-mono text-sm">35%</div>
                <div>
                  <h4 className="font-bold text-white text-base">Required Skill Coverage</h4>
                  <p className="text-xs text-slate-400">Normalized exact and alias matching across mandatory technical requirements.</p>
                </div>
              </div>

              <div className="flex items-start space-x-4 p-4 rounded-xl glass-panel">
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 font-bold font-mono text-sm">25%</div>
                <div>
                  <h4 className="font-bold text-white text-base">Preferred Skill Bonus</h4>
                  <p className="text-xs text-slate-400">Additional credit for secondary framework, tool, and domain expertise.</p>
                </div>
              </div>

              <div className="flex items-start space-x-4 p-4 rounded-xl glass-panel">
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 font-bold font-mono text-sm">20%</div>
                <div>
                  <h4 className="font-bold text-white text-base">Experience Duration Gating</h4>
                  <p className="text-xs text-slate-400">Calculates overlapping career ranges with skill-specific duration checks.</p>
                </div>
              </div>

              <div className="flex items-start space-x-4 p-4 rounded-xl glass-panel">
                <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 font-bold font-mono text-sm">20%</div>
                <div>
                  <h4 className="font-bold text-white text-base">HNSW pgvector Semantic Match</h4>
                  <p className="text-xs text-slate-400">1536-dimensional cosine similarity indexing across candidate resume context.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel p-8 rounded-2xl border border-slate-800 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h4 className="text-lg font-bold text-white">Score Explanation Card</h4>
                <div className="text-xs text-slate-400">Candidate ID: #CAN-9942</div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-black text-sky-400">94.2 / 100</div>
                <div className="text-[10px] font-mono text-emerald-400">RANK #1 • ELIGIBLE</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="text-xs font-bold text-slate-300">Requirement Match Breakdown:</div>
              <div className="text-xs text-slate-400 flex justify-between">
                <span>FastAPI / Python:</span>
                <span className="text-emerald-400 font-mono">Matched (6.5 Yrs)</span>
              </div>
              <div className="text-xs text-slate-400 flex justify-between">
                <span>PostgreSQL / pgvector:</span>
                <span className="text-emerald-400 font-mono">Matched (4.0 Yrs)</span>
              </div>
              <div className="text-xs text-slate-400 flex justify-between">
                <span>Docker & Kubernetes:</span>
                <span className="text-emerald-400 font-mono">Matched (3.5 Yrs)</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
              <div className="text-xs font-bold text-slate-300 mb-1">Quote Evidence Verification:</div>
              <p className="text-xs text-slate-400 italic">
                &quot;Developed low-latency FastAPI services using async PostgreSQL connection pooling and pgvector indexing.&quot;
              </p>
              <div className="mt-2 text-[10px] font-mono text-sky-400 flex items-center justify-between">
                <span>Source: Resume PDF Page 2</span>
                <span className="text-emerald-400 font-bold">Verified Exact Match</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- RECRUITMENT WORKFLOW ---------------------------------------------------------------- */}
      <section id="workflow" className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono text-sky-400 uppercase tracking-widest mb-3">Complete Lifecycle Management</h2>
          <h3 className="text-3xl md:text-5xl font-black text-white tracking-tight">End-to-End Recruitment Workflow</h3>
          <p className="text-slate-300 mt-4 text-base md:text-lg">
            Track candidates seamlessly from initial submission through evidence review, offer issuance, and final placement.
          </p>
        </div>

        {/* Workflow Stages Grid */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs font-mono text-slate-400 mb-1">STAGE 1</div>
            <div className="text-sm font-extrabold text-white">SUBMITTED</div>
            <div className="text-[10px] text-slate-400 mt-2">Resume Upload & Parsing</div>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs font-mono text-sky-400 mb-1">STAGE 2</div>
            <div className="text-sm font-extrabold text-white">RECRUITER REVIEW</div>
            <div className="text-[10px] text-slate-400 mt-2">Score Breakdown Inspection</div>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs font-mono text-indigo-400 mb-1">STAGE 3</div>
            <div className="text-sm font-extrabold text-white">SHORTLISTED</div>
            <div className="text-[10px] text-slate-400 mt-2">Recruiter Human Decision</div>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs font-mono text-purple-400 mb-1">STAGE 4</div>
            <div className="text-sm font-extrabold text-white">OFFER CREATED</div>
            <div className="text-[10px] text-slate-400 mt-2">Offer Terms & Approval</div>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs font-mono text-amber-400 mb-1">STAGE 5</div>
            <div className="text-sm font-extrabold text-white">OFFER ACCEPTED</div>
            <div className="text-[10px] text-slate-400 mt-2">Candidate Formal Sign-off</div>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-emerald-500/40 bg-emerald-500/5 text-center">
            <div className="text-xs font-mono text-emerald-400 mb-1">STAGE 6</div>
            <div className="text-sm font-extrabold text-emerald-300">HIRED</div>
            <div className="text-[10px] text-emerald-400/80 mt-2">Placement & Fill Metrics</div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- RECRUITER VS CANDIDATE PORTALS ---------------------------------------------------------------- */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Recruiter Card */}
          <div className="glass-panel p-8 md:p-10 rounded-3xl border border-slate-800 relative overflow-hidden flex flex-col justify-between">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <svg className="w-40 h-40 text-sky-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
              </svg>
            </div>

            <div>
              <span className="px-3 py-1 rounded-full bg-sky-500/10 text-sky-400 text-xs font-mono font-bold uppercase tracking-wider">
                Recruiter Portal
              </span>
              <h3 className="text-2xl md:text-4xl font-extrabold text-white mt-4 mb-4">
                Evidence-Backed Hiring Control
              </h3>
              <p className="text-slate-300 text-sm leading-relaxed mb-6">
                Manage requisitions, review 4-factor match breakdowns, inspect quote verification, execute decisions, track offers, and export SLA reports.
              </p>

              <ul className="space-y-2.5 text-xs text-slate-300 mb-8">
                <li className="flex items-center space-x-2">
                  <span className="text-sky-400 font-bold">✓</span>
                  <span>1-Click ADVANCE / REJECT / HOLD recruiter decisions</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-sky-400 font-bold">✓</span>
                  <span>Requisition reporting with Time-to-Fill & Time-to-Hire</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-sky-400 font-bold">✓</span>
                  <span>Full immutable audit history per candidate decision</span>
                </li>
              </ul>
            </div>

            <Link
              href="/recruiter/dashboard"
              className="inline-flex items-center justify-center px-6 py-3 text-sm font-bold rounded-xl btn-shimmer text-white shadow-lg"
            >
              Launch Recruiter Dashboard →
            </Link>
          </div>

          {/* Candidate Card */}
          <div className="glass-panel p-8 md:p-10 rounded-3xl border border-slate-800 relative overflow-hidden flex flex-col justify-between">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <svg className="w-40 h-40 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
              </svg>
            </div>

            <div>
              <span className="px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-xs font-mono font-bold uppercase tracking-wider">
                Candidate Portal
              </span>
              <h3 className="text-2xl md:text-4xl font-extrabold text-white mt-4 mb-4">
                Transparent Career Portal
              </h3>
              <p className="text-slate-300 text-sm leading-relaxed mb-6">
                Build reusable profile, parse PDF resumes, calculate experience automatically, apply to open jobs, and track application status.
              </p>

              <ul className="space-y-2.5 text-xs text-slate-300 mb-8">
                <li className="flex items-center space-x-2">
                  <span className="text-indigo-400 font-bold">✓</span>
                  <span>Instant PDF resume parsing & experience calculation</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-indigo-400 font-bold">✓</span>
                  <span>Real-time application status & offer acceptance</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="text-indigo-400 font-bold">✓</span>
                  <span>Assessment workflow & video meeting links</span>
                </li>
              </ul>
            </div>

            <Link
              href="/candidate/dashboard"
              className="inline-flex items-center justify-center px-6 py-3 text-sm font-bold rounded-xl glass-panel-hover text-white border border-slate-700"
            >
              Launch Candidate Portal →
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- PROMINENT AI GOVERNANCE ---------------------------------------------------------------- */}
      <section id="governance" className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="p-8 md:p-14 rounded-3xl bg-gradient-to-br from-indigo-950/80 via-slate-900 to-slate-950 border-2 border-indigo-500/40 shadow-2xl relative overflow-hidden">
          <div className="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />

          <div className="max-w-3xl">
            <span className="px-3.5 py-1.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-mono font-bold uppercase tracking-widest border border-indigo-500/30">
              CORE GOVERNANCE PRINCIPLE
            </span>
            <h2 className="text-4xl md:text-6xl font-black text-white tracking-tight mt-4 mb-6">
              &quot;AI ASSISTS. <span className="text-gradient-cyan">RECRUITER DECIDES.&quot;</span>
            </h2>
            <p className="text-slate-300 text-base md:text-lg leading-relaxed mb-8">
              Our AI architecture is built on absolute recruiter supremacy. Generative AI and vector search provide explainable insights and evidence recommendations—but **0% state mutation authority**.
            </p>

            <div className="grid sm:grid-cols-2 gap-4 text-xs font-medium text-slate-300">
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
                <span className="text-emerald-400 font-extrabold text-lg">0</span>
                <span>AI Mutation Paths (Blocked by System Architecture)</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
                <span className="text-sky-400 font-extrabold text-lg">100%</span>
                <span>Human Recruiter Decision Authority</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
                <span className="text-indigo-400 font-extrabold text-lg">✓</span>
                <span>Protected Attribute Masking (Age/Race/Gender)</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
                <span className="text-purple-400 font-extrabold text-lg">✓</span>
                <span>Immutable Decision Audit Logging</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- ENTERPRISE SECURITY ---------------------------------------------------------------- */}
      <section id="security" className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-mono text-sky-400 uppercase tracking-widest mb-3">Hardened SaaS Security</h2>
          <h3 className="text-3xl md:text-5xl font-black text-white tracking-tight">Enterprise Infrastructure & Compliance</h3>
          <p className="text-slate-300 mt-4 text-base md:text-lg">
            Multi-tenant isolation, cryptographic webhook signatures, and automated audit streaming built for scale.
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h4 className="font-bold text-white text-base mb-2">PostgreSQL RLS</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              `FORCE ROW LEVEL SECURITY` enforced on every database transaction via `set_tenant_context()`.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h4 className="font-bold text-white text-base mb-2">HMAC-SHA256 Webhooks</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Cryptographically signed events with 300s replay window and isolated secret rotation.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h4 className="font-bold text-white text-base mb-2">Rate Limiting Quotas</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Multi-tier request protection with `Retry-After` headers and complete tenant quota isolation.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-slate-800">
            <h4 className="font-bold text-white text-base mb-2">CloudWatch / SIEM</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Structured audit streaming to CloudWatch log streams with sanitized PII/secret removal.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- FINAL CTA ---------------------------------------------------------------- */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
        <div className="p-12 rounded-3xl glass-panel border border-slate-800 relative overflow-hidden">
          <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight mb-6">
            Ready to transform enterprise hiring?
          </h2>
          <p className="text-slate-300 text-base md:text-lg max-w-2xl mx-auto mb-8">
            Experience evidence-backed AI recruitment with complete governance and tenant isolation.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/recruiter/dashboard"
              className="w-full sm:w-auto px-8 py-4 text-base font-bold rounded-xl btn-shimmer text-white shadow-xl shadow-sky-500/25"
            >
              Recruiter Dashboard →
            </Link>

            <Link
              href="/candidate/dashboard"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold rounded-xl glass-panel-hover text-slate-200 border border-slate-700"
            >
              Candidate Portal
            </Link>

            <Link
              href="/admin/dashboard"
              className="w-full sm:w-auto px-6 py-4 text-base font-mono text-slate-400 hover:text-white transition-colors"
            >
              Platform Admin
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- FOOTER ---------------------------------------------------------------- */}
      <footer className="border-t border-slate-800 bg-slate-950 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center text-white font-bold text-sm">
              AH
            </div>
            <span className="text-sm font-bold text-slate-200">AuraHire AI Enterprise SaaS</span>
            <span className="text-xs font-mono text-slate-500">v1.0.0</span>
          </div>

          <div className="flex items-center space-x-6 text-xs text-slate-400">
            <Link href="/recruiter/dashboard" className="hover:text-white transition-colors">Recruiter</Link>
            <Link href="/candidate/dashboard" className="hover:text-white transition-colors">Candidate</Link>
            <Link href="/admin/dashboard" className="hover:text-white transition-colors">Admin</Link>
          </div>

          <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
