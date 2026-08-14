"use client";

import React, { useState } from "react";
import Link from "next/link";

interface CandidateInterviewRow {
  id: string;
  interview_type: string;
  scheduled_at: string;
  timezone: string;
  meeting_url: string;
  status: string;
}

export default function CandidateInterviewsPage() {
  const [interviews] = useState<CandidateInterviewRow[]>([
    {
      id: "int-101",
      interview_type: "TECHNICAL",
      scheduled_at: "2026-08-16 10:00 AM",
      timezone: "America/Chicago",
      meeting_url: "https://meet.internal/test-room/fc0f6a74d1",
      status: "SCHEDULED",
    },
  ]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Scheduled Interviews</h1>
            <p className="text-slate-400 text-xs mt-1">Review meeting dates, times, timezones, and join video conference rooms.</p>
          </div>
          <Link href="/candidate/dashboard" className="text-xs text-slate-400 hover:underline">
            &larr; Candidate Dashboard
          </Link>
        </div>

        {interviews.length === 0 ? (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center">
            <div className="text-slate-400 font-medium">No interviews scheduled</div>
            <p className="text-slate-500 text-xs mt-1">Interviews scheduled by hiring organizations will appear here.</p>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                  <th className="p-4">Type</th>
                  <th className="p-4">Scheduled Date & Time</th>
                  <th className="p-4">Timezone</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Join Meeting</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {interviews.map((i) => (
                  <tr key={i.id} className="hover:bg-slate-900/50">
                    <td className="p-4 font-semibold text-white">{i.interview_type}</td>
                    <td className="p-4 text-slate-300">{i.scheduled_at}</td>
                    <td className="p-4 text-slate-400 font-mono">{i.timezone}</td>
                    <td className="p-4">
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {i.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <a
                        href={i.meeting_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold shadow-md transition-all"
                      >
                        Join Room &rarr;
                      </a>
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
