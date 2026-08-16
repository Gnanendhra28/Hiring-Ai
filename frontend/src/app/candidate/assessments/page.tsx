"use client";

import React, { useState } from "react";
import Link from "next/link";

interface AssessmentItem {
  id: string;
  title: string;
  company: string;
  duration: string;
  assignedAt: string;
  dueAt: string;
  status: "PENDING" | "COMPLETED";
}

export default function CandidateAssessmentsPage() {
  const [assessments, setAssessments] = useState<AssessmentItem[]>([
    {
      id: "ass-101",
      title: "Full Stack Systems & Async Architecture Challenge",
      company: "Nexus Hiring AI",
      duration: "45 Minutes",
      assignedAt: "Aug 14, 2026",
      dueAt: "Aug 21, 2026 (Due in 5 days)",
      status: "PENDING",
    },
    {
      id: "ass-102",
      title: "Frontend Vector Normalization & State Management Test",
      company: "Acme Cloud Corp",
      duration: "30 Minutes",
      assignedAt: "Aug 10, 2026",
      dueAt: "Aug 16, 2026",
      status: "COMPLETED",
    },
  ]);

  const handleStart = (id: string) => {
    setAssessments(
      assessments.map((a) => (a.id === id ? { ...a, status: "COMPLETED" } : a))
    );
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-mono mb-2">
            <span>TECHNICAL ASSESSMENTS</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Assigned Assessments</h1>
          <p className="text-slate-400 text-xs mt-1">Complete your technical coding tests and skill evaluations before the specified deadlines.</p>
        </div>

        <Link
          href="/candidate/dashboard"
          className="text-xs font-mono text-slate-400 hover:text-white hover:underline self-start sm:self-auto"
        >
          ← Return to Dashboard
        </Link>
      </div>

      {/* Assessment Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {assessments.map((item) => (
          <div
            key={item.id}
            className="glass-panel rounded-3xl p-6 border border-slate-800 space-y-5 flex flex-col justify-between hover:border-slate-700 transition-all"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase text-slate-500">{item.company}</span>
                <span
                  className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full font-bold border ${
                    item.status === "COMPLETED"
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                      : "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
                  }`}
                >
                  {item.status === "COMPLETED" ? "Completed ✓" : "Action Required"}
                </span>
              </div>

              <h2 className="text-base font-bold text-white leading-snug">{item.title}</h2>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-400 pt-2 border-t border-slate-800/80">
                <div>
                  <span className="text-slate-500 block text-[10px]">TIME ALLOTTED</span>
                  <span className="text-slate-200">{item.duration}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">DEADLINE</span>
                  <span className="text-slate-200">{item.dueAt}</span>
                </div>
              </div>
            </div>

            <div className="pt-4">
              {item.status === "PENDING" ? (
                <button
                  onClick={() => handleStart(item.id)}
                  className="w-full py-3 px-4 rounded-xl btn-shimmer font-bold text-white text-xs shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center space-x-2"
                >
                  <span>Start Assessment Now</span>
                  <span className="font-mono">→</span>
                </button>
              ) : (
                <div className="py-2.5 px-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold text-center">
                  Score Verified &amp; Submitted to Recruiter ✓
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
