"use client";

import React, { useState } from "react";
import Link from "next/link";

interface ApplicationRow {
  id: string;
  job_title: string;
  organization_name: string;
  submitted_at: string;
  status: string;
}

export default function CandidateApplicationsPage() {
  const [applications] = useState<ApplicationRow[]>([]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Application Tracker</h1>
            <p className="text-slate-400 text-xs mt-1">Review the live status of all your submitted job applications.</p>
          </div>
          <Link
            href="/jobs"
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded-lg transition-colors"
          >
            + Apply for Jobs
          </Link>
        </div>

        {applications.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center">
            <div className="text-slate-400 font-medium">No application records found</div>
            <p className="text-slate-500 text-xs mt-1">You haven&apos;t submitted any job applications yet.</p>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                  <th className="p-4">Position</th>
                  <th className="p-4">Company</th>
                  <th className="p-4">Submitted Date</th>
                  <th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {applications.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-900/50">
                    <td className="p-4 font-medium text-white">{a.job_title}</td>
                    <td className="p-4 text-slate-400">{a.organization_name}</td>
                    <td className="p-4 text-slate-400">{a.submitted_at}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {a.status}
                      </span>
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
