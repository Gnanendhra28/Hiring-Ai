"use client";

import React, { useState } from "react";
import Link from "next/link";

interface PendingAdminJob {
  id: string;
  title: string;
  organization_name: string;
  department: string | null;
  employment_type: string;
  created_at: string;
}

export default function AdminJobsQueuePage() {
  const [jobs] = useState<PendingAdminJob[]>([]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Pending Job Verification Queue</h1>
            <p className="text-slate-400 text-xs mt-1">Review job requisitions submitted by recruiter organizations across the platform.</p>
          </div>
          <Link href="/admin/dashboard" className="text-xs text-slate-400 hover:underline">
            &larr; Admin Dashboard
          </Link>
        </div>

        {jobs.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center">
            <div className="text-slate-400 font-medium">No job requisitions pending review</div>
            <p className="text-slate-500 text-xs mt-1">All recruiter job submissions have been verified and processed.</p>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                  <th className="p-4">Title</th>
                  <th className="p-4">Organization</th>
                  <th className="p-4">Department</th>
                  <th className="p-4">Type</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-900/50">
                    <td className="p-4 font-medium text-white">{j.title}</td>
                    <td className="p-4 text-slate-400">{j.organization_name}</td>
                    <td className="p-4 text-slate-400">{j.department || "General"}</td>
                    <td className="p-4 text-slate-400">{j.employment_type}</td>
                    <td className="p-4 text-right">
                      <Link
                        href={`/admin/jobs/${j.id}`}
                        className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-[11px] font-semibold transition-all"
                      >
                        Inspect & Verify
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
