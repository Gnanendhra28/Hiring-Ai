"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface InterviewRow {
  id: string;
  candidate_name: string;
  interview_type: string;
  scheduled_at: string;
  timezone: string;
  meeting_url: string;
  status: string;
}

export default function RecruiterInterviewsPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [interviews] = useState<InterviewRow[]>([
    {
      id: "int-101",
      candidate_name: "Jane Candidate",
      interview_type: "TECHNICAL",
      scheduled_at: "2026-08-16 10:00 AM",
      timezone: "America/Chicago",
      meeting_url: "https://meet.internal/test-room/fc0f6a74d1",
      status: "SCHEDULED",
    },
  ]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Job Requisition
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Scheduled Interviews</h1>
            <p className="text-slate-400 text-xs">Manage interviewer schedules and video meeting room links.</p>
          </div>
        </div>

        {/* Interviews List */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                <th className="p-4">Candidate</th>
                <th className="p-4">Type</th>
                <th className="p-4">Scheduled Date & Time</th>
                <th className="p-4">Timezone</th>
                <th className="p-4">Meeting URL</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {interviews.map((i) => (
                <tr key={i.id} className="hover:bg-slate-900/50">
                  <td className="p-4 font-semibold text-white">{i.candidate_name}</td>
                  <td className="p-4 text-slate-300">{i.interview_type}</td>
                  <td className="p-4 text-slate-300">{i.scheduled_at}</td>
                  <td className="p-4 text-slate-400 font-mono">{i.timezone}</td>
                  <td className="p-4">
                    <a
                      href={i.meeting_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline font-mono"
                    >
                      Join Meeting &rarr;
                    </a>
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {i.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
