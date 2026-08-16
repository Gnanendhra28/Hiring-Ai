"use client";

import React, { useState } from "react";
import Link from "next/link";

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
  const [applications] = useState<ApplicationRecord[]>([
    {
      id: "app-101",
      jobTitle: "Senior Frontend Architect",
      organizationName: "Acme Cloud Corp",
      submittedAt: "Aug 12, 2026",
      status: "Interview Scheduled",
      stage: "Stage 4 of 5: Technical Interview",
      matchScore: 96,
      location: "San Francisco, CA (Remote)",
    },
    {
      id: "app-102",
      jobTitle: "Staff AI Systems Engineer",
      organizationName: "Nexus Hiring AI",
      submittedAt: "Aug 14, 2026",
      status: "Assessment Pending",
      stage: "Stage 3 of 5: Coding Challenge",
      matchScore: 92,
      location: "Bangalore, India",
    },
    {
      id: "app-103",
      jobTitle: "Lead Full Stack Developer",
      organizationName: "Vortex Scale Labs",
      submittedAt: "Aug 15, 2026",
      status: "Under Review",
      stage: "Stage 2 of 5: Recruiter Review",
      matchScore: 88,
      location: "New York, NY (Hybrid)",
    },
  ]);

  const filteredApps = applications.filter((app) => {
    if (filter === "active") return app.status !== "Rejected" && app.status !== "Hired";
    if (filter === "completed") return app.status === "Hired" || app.status === "Rejected";
    return true;
  });

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono mb-2">
            <span>APPLICATION TRACKER</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">My Submissions</h1>
          <p className="text-slate-400 text-xs mt-1">Review live recruitment stage progression and match analytics for all your job applications.</p>
        </div>

        <Link
          href="/jobs"
          className="py-3 px-5 rounded-xl btn-shimmer font-bold text-white shadow-lg shadow-sky-500/20 text-xs transition-all self-start sm:self-auto"
        >
          + Explore Open Positions
        </Link>
      </div>

      {/* Filters Bar */}
      <div className="flex items-center space-x-2">
        {(["all", "active", "completed"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold capitalize transition-all ${
              filter === tab
                ? "bg-slate-900 text-sky-400 border border-slate-800 shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {tab} Applications
          </button>
        ))}
      </div>

      {/* Applications Table Card */}
      <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase font-mono tracking-wider">
                <th className="p-4 pl-6">Job Position &amp; Company</th>
                <th className="p-4">Submitted Date</th>
                <th className="p-4">Current Stage</th>
                <th className="p-4">Match Alignment</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredApps.map((a) => (
                <tr key={a.id} className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-4 pl-6">
                    <div className="font-bold text-white text-sm">{a.jobTitle}</div>
                    <div className="text-slate-400 font-mono text-[11px] mt-0.5">{a.organizationName} • {a.location}</div>
                  </td>
                  <td className="p-4 font-mono text-slate-300">{a.submittedAt}</td>
                  <td className="p-4">
                    <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-medium">
                      <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                      <span>{a.status}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono mt-1">{a.stage}</div>
                  </td>
                  <td className="p-4">
                    <span className="font-mono font-bold text-emerald-400 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      {a.matchScore}% Match
                    </span>
                  </td>
                  <td className="p-4 pr-6 text-right">
                    <Link
                      href="/candidate/dashboard"
                      className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-mono text-[11px] transition-colors inline-block"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
