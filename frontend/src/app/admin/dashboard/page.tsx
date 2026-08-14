"use client";

import React, { useState } from "react";
import Link from "next/link";

interface PendingJobSummary {
  id: string;
  title: string;
  organization_name: string;
  submitted_at: string;
}

export default function AdminDashboardPage() {
  const [pendingJobs] = useState<PendingJobSummary[]>([]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider">
                Platform Admin
              </span>
            </div>
            <h1 className="text-3xl font-bold text-white mt-1">Admin Verification Portal</h1>
            <p className="text-slate-400 text-sm mt-1">Inspect and approve job requisitions created by recruiter organizations before public publication.</p>
          </div>
          <Link
            href="/admin/jobs"
            className="text-xs bg-amber-600 hover:bg-amber-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors shadow-md shadow-amber-600/20"
          >
            Review Pending Queue &rarr;
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
            <div className="text-xs text-slate-400 font-medium">Pending Verifications</div>
            <div className="text-3xl font-bold text-amber-400 mt-2">{pendingJobs.length}</div>
            <div className="text-[11px] text-slate-500 mt-1">Requisitions awaiting review</div>
          </div>
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
            <div className="text-xs text-slate-400 font-medium">Verified & Approved Jobs</div>
            <div className="text-3xl font-bold text-emerald-400 mt-2">0</div>
            <div className="text-[11px] text-slate-500 mt-1">Platform-wide approved postings</div>
          </div>
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
            <div className="text-xs text-slate-400 font-medium">Rejected Requisitions</div>
            <div className="text-3xl font-bold text-rose-400 mt-2">0</div>
            <div className="text-[11px] text-slate-500 mt-1">Returned for recruiter revision</div>
          </div>
        </div>

        {/* Pending Requisitions Table / Clean Empty State */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Pending Verification Queue</h2>
          {pendingJobs.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-800 rounded-lg">
              <div className="text-slate-400 font-medium text-sm">No job requisitions awaiting admin verification</div>
              <p className="text-slate-500 text-xs mt-1">All submitted recruiter requisitions have been processed.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {pendingJobs.map((j) => (
                <div key={j.id} className="py-4 flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-white">{j.title}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{j.organization_name} &bull; Submitted {j.submitted_at}</div>
                  </div>
                  <Link
                    href={`/admin/jobs/${j.id}`}
                    className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-md transition-colors"
                  >
                    Inspect & Verify &rarr;
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
