"use client";

import React, { useState } from "react";
import Link from "next/link";

interface InterviewItem {
  id: string;
  type: string;
  jobTitle: string;
  company: string;
  scheduledAt: string;
  timezone: string;
  meetingUrl: string;
  interviewerName: string;
  status: "SCHEDULED" | "COMPLETED" | "RESCHEDULED";
}

export default function CandidateInterviewsPage() {
  const [interviews] = useState<InterviewItem[]>([
    {
      id: "int-101",
      type: "Technical Systems Architecture Interview",
      jobTitle: "Senior Frontend Architect",
      company: "Acme Cloud Corp",
      scheduledAt: "Tomorrow at 2:00 PM IST (Aug 17, 2026)",
      timezone: "Asia/Kolkata (IST)",
      meetingUrl: "https://meet.internal/test-room/fc0f6a74d1",
      interviewerName: "Dr. Sarah Jenkins (VP of Engineering)",
      status: "SCHEDULED",
    },
  ]);

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mb-2">
            <span>INTERVIEW ROOMS</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Scheduled Interviews</h1>
          <p className="text-slate-400 text-xs mt-1">Review confirmed meeting dates, interviewer profiles, and launch your video conference room.</p>
        </div>

        <Link
          href="/candidate/dashboard"
          className="text-xs font-mono text-slate-400 hover:text-white hover:underline self-start sm:self-auto"
        >
          ← Return to Dashboard
        </Link>
      </div>

      {/* Interviews List */}
      <div className="space-y-6">
        {interviews.map((item) => (
          <div
            key={item.id}
            className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6 hover:border-slate-700 transition-all"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-3">
                  <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
                    {item.status}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">{item.company}</span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">{item.type}</h2>
                <div className="text-xs text-slate-400 mt-0.5">{item.jobTitle} • Interviewer: {item.interviewerName}</div>
              </div>

              <div className="flex items-center space-x-3">
                <a
                  href={item.meetingUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="py-3 px-6 rounded-xl btn-shimmer font-bold text-white text-xs shadow-lg shadow-sky-500/20 transition-all flex items-center space-x-2"
                >
                  <span>Launch Video Room</span>
                  <span className="font-mono">→</span>
                </a>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800/80 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">SCHEDULED TIME</span>
                <span className="text-slate-200 font-bold">{item.scheduledAt}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">TIMEZONE</span>
                <span className="text-slate-200">{item.timezone}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">VERIFICATION STATUS</span>
                <span className="text-emerald-400 font-bold">Calendar Confirmed ✓</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
