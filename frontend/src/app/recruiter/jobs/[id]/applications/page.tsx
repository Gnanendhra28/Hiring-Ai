"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface RecruiterApplicationRow {
  id: string;
  candidate_name: string;
  candidate_email: string;
  headline: string;
  skills: string[];
  submitted_at: string;
  status: "SUBMITTED" | "RECRUITER_REVIEW" | "SHORTLISTED" | "REJECTED";
}

export default function RecruiterApplicationPipelinePage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [applications] = useState<RecruiterApplicationRow[]>([
    {
      id: "app-101",
      candidate_name: "Jane Candidate",
      candidate_email: "jane.candidate@example.com",
      headline: "Senior Full-Stack Developer",
      skills: ["Python", "FastAPI", "React", "PostgreSQL"],
      submitted_at: "2026-08-14T12:00:00Z",
      status: "SUBMITTED",
    },
  ]);

  const [selectedApp, setSelectedApp] = useState<RecruiterApplicationRow | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [decisionReason, setDecisionReason] = useState("");

  const filteredApps = applications.filter((app) => {
    const matchesSearch =
      app.candidate_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.headline.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDecision = (newStatus: "SHORTLISTED" | "REJECTED") => {
    if (selectedApp) {
      selectedApp.status = newStatus;
      setSelectedApp(null);
      setDecisionReason("");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Job Requisition
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Application Pipeline</h1>
            <p className="text-slate-400 text-xs">Manage candidate submissions and make human hiring decisions.</p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">{filteredApps.length} Submissions</span>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center gap-4">
          <input
            type="text"
            placeholder="Search candidates by name, headline, or skill..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          />

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Application States</option>
            <option value="SUBMITTED">SUBMITTED</option>
            <option value="RECRUITER_REVIEW">RECRUITER REVIEW</option>
            <option value="SHORTLISTED">SHORTLISTED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>

        {/* Server-Side Paginated Applications Table */}
        {filteredApps.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center">
            <div className="text-slate-400 font-medium">No candidates matching pipeline criteria</div>
            <p className="text-slate-500 text-xs mt-1">Submissions to this requisition will appear here.</p>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                  <th className="p-4">Candidate</th>
                  <th className="p-4">Headline</th>
                  <th className="p-4">Skills</th>
                  <th className="p-4">Submitted Date</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filteredApps.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-900/50">
                    <td className="p-4 font-semibold text-white">
                      <div>{app.candidate_name}</div>
                      <div className="text-[11px] text-slate-400">{app.candidate_email}</div>
                    </td>
                    <td className="p-4 text-slate-300">{app.headline}</td>
                    <td className="p-4">
                      <div className="flex flex-wrap gap-1">
                        {app.skills.map((s, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">
                            {s}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="p-4 text-slate-400">{app.submitted_at}</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold border ${
                        app.status === "SHORTLISTED"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : app.status === "REJECTED"
                          ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                          : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                      }`}>
                        {app.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => setSelectedApp(app)}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold transition-all"
                      >
                        Inspect Candidate &rarr;
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Candidate Detail & Human Decision Drawer Modal */}
        {selectedApp && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-2xl w-full space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedApp.candidate_name}</h3>
                  <p className="text-xs text-slate-400">{selectedApp.headline} &bull; {selectedApp.candidate_email}</p>
                </div>
                <button onClick={() => setSelectedApp(null)} className="text-slate-400 hover:text-white text-sm">
                  ✕
                </button>
              </div>

              {/* Factual Candidate Profile Data */}
              <div className="space-y-4 text-xs">
                <div>
                  <div className="font-semibold text-slate-300 uppercase tracking-wider mb-1">Skills & Technical Competencies</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedApp.skills.map((s, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="font-semibold text-slate-300 uppercase tracking-wider mb-1">Document Reference</div>
                  <div className="text-slate-400">📄 Resume File: <code className="text-blue-400 bg-slate-950 px-2 py-0.5 rounded">candidates/docs/resume.pdf</code></div>
                </div>

                <div>
                  <div className="font-semibold text-slate-300 uppercase tracking-wider mb-1">Human Recruiter Decision</div>
                  <textarea
                    rows={3}
                    value={decisionReason}
                    onChange={(e) => setDecisionReason(e.target.value)}
                    placeholder="Optional notes regarding shortlist or rejection decision..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Human Decision Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-800">
                <button
                  onClick={() => setSelectedApp(null)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-lg"
                >
                  Close Detail
                </button>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleDecision("REJECTED")}
                    className="px-4 py-2 bg-rose-600/20 border border-rose-500/30 hover:bg-rose-600/30 text-rose-300 text-xs font-semibold rounded-lg transition-all"
                  >
                    Reject Candidate
                  </button>
                  <button
                    onClick={() => handleDecision("SHORTLISTED")}
                    className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all"
                  >
                    Shortlist Candidate
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
