"use client";

import React, { useState } from "react";
import Link from "next/link";

interface JobItem {
  id: string;
  title: string;
  department: string | null;
  location: string | null;
  employment_type: string;
  status: string;
  created_at: string;
}

export default function JobWorkspaceListPage() {
  const [jobs] = useState<JobItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Job Workspace</h1>
            <p className="text-slate-400 text-sm mt-1">Manage active requisitions, draft descriptions, and candidate pipelines.</p>
          </div>
          <Link
            href="/recruiter/jobs/new"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg text-sm shadow-md transition-all self-start md:self-auto"
          >
            + New Requisition
          </Link>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3">
          {["ALL", "PUBLISHED", "DRAFT", "PAUSED", "CLOSED"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterStatus === st
                  ? "bg-blue-600 text-white"
                  : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Jobs List / Empty State */}
        {jobs.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center">
            <div className="text-slate-400 font-medium text-base">No job requisitions found</div>
            <p className="text-slate-500 text-xs mt-1 max-w-sm mx-auto">
              Create a job requisition to define job requirements, activate tenant vector indexes, and prepare candidate application streams.
            </p>
            <Link
              href="/recruiter/jobs/new"
              className="inline-block mt-4 text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded-lg transition-colors"
            >
              Create First Job
            </Link>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                  <th className="p-4">Title</th>
                  <th className="p-4">Department</th>
                  <th className="p-4">Location</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="p-4 font-medium text-white">
                      <Link href={`/recruiter/jobs/${job.id}`} className="hover:underline text-blue-400">
                        {job.title}
                      </Link>
                    </td>
                    <td className="p-4 text-slate-400">{job.department || "N/A"}</td>
                    <td className="p-4 text-slate-400">{job.location || "Remote"}</td>
                    <td className="p-4 text-slate-400">{job.employment_type}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {job.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <Link href={`/recruiter/jobs/${job.id}`} className="text-xs text-slate-400 hover:text-white">
                        Open Workspace &rarr;
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
