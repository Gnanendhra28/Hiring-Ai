"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Award, CheckCircle, Lightbulb, Sparkles, Target, Zap } from "lucide-react";

export default function CareerPage() {
  return (
    <div className="h-page space-y-6">
      {/* Header */}
      <section className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow">AI Career Guidance</p>
          <h1 className="page-title">Career Progression &amp; Skill Insights</h1>
          <p className="page-subtitle">AI-driven analysis of your profile readiness, skill gaps, and target role trajectory.</p>
        </div>
        <Link href="/jobs" className="h-btn">
          Explore Matched Jobs <ArrowRight size={15} />
        </Link>
      </section>

      {/* Hero Analytics Card */}
      <section className="h-card ai-card p-6 sm:p-8 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <span className="h-chip bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-400 font-bold">
              AI Match Score Readiness
            </span>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
              82 / 100 Profile Strength
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 max-w-xl">
              Your background in Python 3.13, FastAPI, and RAG architectures places you in the top 8% of candidates for Generative AI Engineer positions.
            </p>
          </div>

          <div className="flex items-center gap-6 p-4 rounded-xl bg-white/60 dark:bg-slate-900/60 border border-indigo-200 dark:border-indigo-900">
            <div className="text-center">
              <strong className="block text-2xl text-emerald-600 dark:text-emerald-400 font-extrabold">94%</strong>
              <span className="text-[10px] font-bold uppercase text-slate-500">AI/ML Engineer</span>
            </div>
            <div className="w-px h-10 bg-slate-200 dark:bg-slate-800" />
            <div className="text-center">
              <strong className="block text-2xl text-indigo-600 dark:text-indigo-400 font-extrabold">91%</strong>
              <span className="text-[10px] font-bold uppercase text-slate-500">Applied AI Engineer</span>
            </div>
          </div>
        </div>
      </section>

      {/* Skill Gaps & Recommendations */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="h-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Target size={18} className="text-indigo-600 dark:text-indigo-400" />
            <h2 className="font-bold text-slate-900 dark:text-white text-base">Key Skill Gaps Identified</h2>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Adding these 2 core competencies will increase your overall AI match score to 96%.
          </p>

          <div className="space-y-3">
            <div className="p-3.5 rounded-lg border border-amber-200 dark:border-amber-900/60 bg-amber-50/50 dark:bg-amber-950/20 text-xs space-y-1">
              <div className="flex items-center justify-between font-bold text-amber-800 dark:text-amber-300">
                <span>Kubernetes &amp; Cloud Deployment</span>
                <span className="text-[10px] bg-amber-200 dark:bg-amber-900/80 px-2 py-0.5 rounded text-amber-900 dark:text-amber-200">High Impact</span>
              </div>
              <p className="text-amber-700 dark:text-amber-400 text-[11px]">
                Requested in 65% of Senior AI Engineer postings across Aster Labs and Northstar.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/50 dark:bg-indigo-950/20 text-xs space-y-1">
              <div className="flex items-center justify-between font-bold text-indigo-800 dark:text-indigo-300">
                <span>AWS SageMaker / Bedrock</span>
                <span className="text-[10px] bg-indigo-200 dark:bg-indigo-900/80 px-2 py-0.5 rounded text-indigo-900 dark:text-indigo-200">Medium Impact</span>
              </div>
              <p className="text-indigo-700 dark:text-indigo-400 text-[11px]">
                Enables eligibility for enterprise cloud deployment roles.
              </p>
            </div>
          </div>
        </div>

        <div className="h-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-emerald-600 dark:text-emerald-400" />
            <h2 className="font-bold text-slate-900 dark:text-white text-base">Verified Strengths</h2>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            These verified technical skills strongly match active open requisitions.
          </p>

          <div className="space-y-2.5">
            {[
              "Python 3.13 & AsyncIO High-Performance Microservices",
              "RAG Architecture & PGVector Embedding Search",
              "FastAPI REST API Design & PostgreSQL Optimization",
              "Docker Containerization & CI/CD Workflows",
            ].map((strength) => (
              <div key={strength} className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300 font-medium p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                <CheckCircle size={15} className="text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span>{strength}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
