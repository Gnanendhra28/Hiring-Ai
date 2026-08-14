"use client";

import React, { useState } from "react";
import Link from "next/link";

interface CandidateAssRow {
  id: string;
  assessment_title: string;
  assigned_at: string;
  due_at: string;
  status: string;
}

export default function CandidateAssessmentsPage() {
  const [assessments, setAssessments] = useState<CandidateAssRow[]>([
    {
      id: "ass-101",
      assessment_title: "Python Backend Systems Architecture Test",
      assigned_at: "2026-08-14",
      due_at: "2026-08-21",
      status: "SENT",
    },
  ]);

  const handleStartTest = (id: string) => {
    setAssessments(
      assessments.map((a) => (a.id === id ? { ...a, status: "COMPLETED" } : a))
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Assigned Technical Assessments</h1>
            <p className="text-slate-400 text-xs mt-1">Complete your technical tests before the specified due date.</p>
          </div>
          <Link href="/candidate/dashboard" className="text-xs text-slate-400 hover:underline">
            &larr; Candidate Dashboard
          </Link>
        </div>

        {assessments.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center">
            <div className="text-slate-400 font-medium">No assigned assessments</div>
            <p className="text-slate-500 text-xs mt-1">Assessments assigned by hiring organizations will appear here.</p>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                  <th className="p-4">Assessment Title</th>
                  <th className="p-4">Assigned Date</th>
                  <th className="p-4">Due Date</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {assessments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-900/50">
                    <td className="p-4 font-semibold text-white">{a.assessment_title}</td>
                    <td className="p-4 text-slate-400">{a.assigned_at}</td>
                    <td className="p-4 text-slate-400">{a.due_at}</td>
                    <td className="p-4">
                      <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold border ${
                        a.status === "COMPLETED"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      {a.status !== "COMPLETED" ? (
                        <button
                          onClick={() => handleStartTest(a.id)}
                          className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold shadow-md transition-all"
                        >
                          Start Test &rarr;
                        </button>
                      ) : (
                        <span className="text-[11px] text-emerald-400 font-semibold">Completed ✓</span>
                      )}
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
