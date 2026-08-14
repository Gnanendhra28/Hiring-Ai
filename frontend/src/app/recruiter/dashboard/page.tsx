"use client";

import React, { useState } from "react";
import Link from "next/link";

interface DashboardMetrics {
  active_jobs_count: number;
  draft_jobs_count: number;
  closed_jobs_count: number;
  total_applications_count: number;
  recent_jobs: Array<{
    id: string;
    title: string;
    department: string | null;
    status: string;
    created_at: string;
  }>;
}

export default function RecruiterDashboardPage() {
  const [metrics] = useState<DashboardMetrics>({
    active_jobs_count: 0,
    draft_jobs_count: 0,
    closed_jobs_count: 0,
    total_applications_count: 0,
    recent_jobs: [],
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Recruiter Workspace</h1>
            <p className="text-slate-400 mt-1">Real-time overview of active requisitions and hiring pipelines.</p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/recruiter/jobs/new"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg shadow-lg shadow-blue-500/20 transition-all text-sm"
            >
              + Post New Job
            </Link>
          </div>
        </div>

        {/* Real Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Requisitions</div>
            <div className="text-4xl font-extrabold text-blue-400 mt-2">{metrics.active_jobs_count}</div>
            <p className="text-xs text-slate-500 mt-1">Live published job openings</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Draft Openings</div>
            <div className="text-4xl font-extrabold text-amber-400 mt-2">{metrics.draft_jobs_count}</div>
            <p className="text-xs text-slate-500 mt-1">Work-in-progress job briefs</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Candidates</div>
            <div className="text-4xl font-extrabold text-emerald-400 mt-2">{metrics.total_applications_count}</div>
            <p className="text-xs text-slate-500 mt-1">Phase 4 ingestion pipeline</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur-sm">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Archived / Closed</div>
            <div className="text-4xl font-extrabold text-slate-400 mt-2">{metrics.closed_jobs_count}</div>
            <p className="text-xs text-slate-500 mt-1">Filled or paused positions</p>
          </div>
        </div>

        {/* Recent Requisitions Section */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Requisitions</h2>
            <Link href="/recruiter/jobs" className="text-xs text-blue-400 hover:underline">
              View all jobs &rarr;
            </Link>
          </div>

          {metrics.recent_jobs.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-800 rounded-lg">
              <div className="text-slate-500 text-sm">No job requisitions created yet in this organization.</div>
              <Link
                href="/recruiter/jobs/new"
                className="inline-block mt-4 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-md transition-colors"
              >
                Create your first job brief
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {metrics.recent_jobs.map((job) => (
                <div key={job.id} className="py-3 flex items-center justify-between">
                  <div>
                    <Link href={`/recruiter/jobs/${job.id}`} className="text-sm font-medium text-blue-400 hover:underline">
                      {job.title}
                    </Link>
                    <div className="text-xs text-slate-400 mt-0.5">{job.department || "General"}</div>
                  </div>
                  <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {job.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
