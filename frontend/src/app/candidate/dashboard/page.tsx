"use client";

import React, { useState } from "react";
import Link from "next/link";

interface CandidateApplication {
  id: string;
  job_title: string;
  organization_name: string;
  status: string;
  submitted_at: string;
}

export default function CandidateDashboardPage() {
  const [applications] = useState<CandidateApplication[]>([]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Candidate Portal</h1>
            <p className="text-slate-400 text-sm mt-1">Track your job applications, professional profile, and hiring status.</p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/candidate/profile"
              className="text-xs bg-slate-900 border border-slate-800 hover:bg-slate-800 px-4 py-2 rounded-lg text-slate-300 transition-colors"
            >
              Edit Profile
            </Link>
            <Link
              href="/jobs"
              className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Browse Open Jobs
            </Link>
          </div>
        </div>

        {/* Real Application Tracker Grid */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">My Active Applications</h2>
            <span className="text-xs text-slate-400">{applications.length} Submissions</span>
          </div>

          {applications.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-800 rounded-lg">
              <div className="text-slate-400 font-medium text-sm">No job applications submitted yet</div>
              <p className="text-slate-500 text-xs mt-1">Browse the public job directory to discover positions matching your skills.</p>
              <Link
                href="/jobs"
                className="inline-block mt-4 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-md transition-colors"
              >
                Browse Jobs
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {applications.map((app) => (
                <div key={app.id} className="py-4 flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-white">{app.job_title}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{app.organization_name} &bull; Submitted {app.submitted_at}</div>
                  </div>
                  <span className="text-xs px-3 py-1 rounded-full font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {app.status}
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
