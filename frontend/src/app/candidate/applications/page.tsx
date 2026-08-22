"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowUpRight, CheckCircle2, Clock, MapPin, Sparkles } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface ApplicationRecord {
  id: string;
  jobTitle: string;
  organizationName: string;
  submittedAt: string;
  status: string;
  stage: string;
  matchScore: number;
  location: string;
}

export default function CandidateApplicationsPage() {
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");
  const [applications, setApplications] = useState<ApplicationRecord[]>([
    {
      id: "app-101",
      jobTitle: "Generative AI Engineer",
      organizationName: "PG - Artificial Intelligence",
      submittedAt: "Aug 20, 2026",
      status: "Interview Scheduled",
      stage: "Stage 3 of 4: AI Technical Interview",
      matchScore: 94,
      location: "Bengaluru, India (Hybrid)",
    },
    {
      id: "app-102",
      jobTitle: "Backend Engineer – Python",
      organizationName: "UG/PG - Computer Science",
      submittedAt: "Aug 18, 2026",
      status: "Under Review",
      stage: "Stage 2 of 4: Recruiter Screening",
      matchScore: 91,
      location: "Remote · India",
    },
    {
      id: "app-103",
      jobTitle: "Machine Learning Engineer",
      organizationName: "Artificial Intelligence Requisition",
      submittedAt: "Aug 15, 2026",
      status: "Application Submitted",
      stage: "Stage 1 of 4: Initial Submission",
      matchScore: 87,
      location: "Pune, India (On-site)",
    },
  ]);

  useEffect(() => {
    async function loadCandidateApplications() {
      try {
        const res = await apiFetch("/api/v1/candidate/applications");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            const formatted = data.map((a: any) => ({
              id: a.id,
              jobTitle: a.job_title || "Engineering Requisition",
              organizationName: a.organization_name || "Enterprise Tenant",
              submittedAt: new Date(a.submitted_at || Date.now()).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              }),
              status: a.status || "Submitted",
              stage: "Stage 2 of 4: In Pipeline",
              matchScore: 90,
              location: a.location || "Remote",
            }));
            setApplications(formatted);
          }
        }
      } catch (err) {
        console.error("Error loading candidate applications:", err);
      }
    }
    loadCandidateApplications();
  }, []);

  const filteredApps = applications.filter((app) => {
    if (filter === "active") return app.status !== "Rejected" && app.status !== "Hired";
    if (filter === "completed") return app.status === "Hired" || app.status === "Rejected";
    return true;
  });

  return (
    <div className="h-page space-y-6">
      {/* Header */}
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow">Application Tracker</p>
          <h1 className="page-title">My Submissions</h1>
          <p className="page-subtitle">Track your recruitment pipeline stages and match scores across all submitted positions.</p>
        </div>

        <Link href="/jobs" className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all">
          + Explore Open Positions
        </Link>
      </section>

      {/* Filter Tabs - Crisp in both Bright and Dark UI */}
      <div className="flex items-center gap-2">
        {(["all", "active", "completed"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold capitalize transition-all ${
              filter === tab
                ? "bg-indigo-600 text-white shadow-xs"
                : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
            }`}
          >
            {tab} Submissions ({applications.length})
          </button>
        ))}
      </div>

      {/* Applications List */}
      <div className="space-y-4">
        {filteredApps.map((app) => (
          <article
            key={app.id}
            className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs hover:shadow-md transition-all"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-3 py-1 rounded-md bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs font-bold">
                    {app.organizationName}
                  </span>
                  <span className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1 font-medium">
                    <Clock size={13} /> Submitted on {app.submittedAt}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {app.jobTitle}
                </h3>

                <p className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1 font-medium">
                  <MapPin size={13} /> {app.location}
                </p>

                <div className="flex items-center gap-2 text-xs pt-1">
                  <span className="px-2.5 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-900 flex items-center gap-1">
                    <CheckCircle2 size={13} /> {app.status}
                  </span>
                  <span className="text-slate-600 dark:text-slate-400 font-semibold">
                    {app.stage}
                  </span>
                </div>
              </div>

              {/* Match Score & Action */}
              <div className="flex md:flex-col items-center md:items-end justify-between gap-3 border-t md:border-t-0 border-slate-100 dark:border-slate-800 pt-3 md:pt-0">
                <div className="text-right">
                  <span className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400">
                    {app.matchScore}%
                  </span>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    AI MATCH SCORE
                  </p>
                </div>

                <Link
                  href={`/jobs/${app.id}`}
                  className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 text-xs font-semibold transition-all flex items-center gap-1"
                >
                  View Details <ArrowUpRight size={14} />
                </Link>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
