"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Play, Calendar, Clock, Award, CheckCircle2, Bot } from "lucide-react";
import { apiFetch } from "@/lib/api";

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
  const [interviews, setInterviews] = useState<InterviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadInterviews() {
      setLoading(true);
      try {
        const res = await apiFetch("/api/v1/candidate/interviews");
        if (res.ok) {
          const data = await res.json();
          const items: InterviewItem[] = await Promise.all(
            data.map(async (i: any) => {
              let jobTitle = "Job Interview";
              let companyName = "Enterprise Partner";
              try {
                const jRes = await apiFetch(`/api/v1/jobs/${i.job_id}`);
                if (jRes.ok) {
                  const jData = await jRes.json();
                  jobTitle = jData.title || jobTitle;
                  companyName = jData.organization_name || companyName;
                }
              } catch {}

              const start = new Date(i.scheduled_start_at);
              return {
                id: i.id,
                type: `${i.interview_type || "TECHNICAL"} AI Assessment & Live Room`,
                jobTitle,
                company: companyName,
                scheduledAt: start.toLocaleDateString("en-US", {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                }),
                timezone: i.timezone || "UTC",
                meetingUrl: `/interview/${i.id}/room`,
                interviewerName: "TalentOS AI Autonomous Agent",
                status: i.status || "SCHEDULED",
              };
            })
          );
          setInterviews(items);
        }
      } catch (err) {
        console.error("Failed loading candidate interviews:", err);
      } finally {
        setLoading(false);
      }
    }
    loadInterviews();
  }, []);

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono mb-2">
            <span>AI INTERVIEW SUITE</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Scheduled Interviews</h1>
          <p className="text-slate-400 text-xs mt-1">
            Review confirmed interview dates, launch your interactive AI interview room, and review evaluations.
          </p>
        </div>

        <Link
          href="/candidate/dashboard"
          className="text-xs font-mono text-slate-400 hover:text-white hover:underline self-start sm:self-auto"
        >
          &larr; Return to Dashboard
        </Link>
      </div>

      {/* Interviews List */}
      <div className="space-y-6">
        {loading ? (
          <div className="glass-panel rounded-3xl p-12 text-center text-slate-400 font-mono text-xs border border-slate-800">
            Loading scheduled interviews...
          </div>
        ) : interviews.length === 0 ? (
          <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 space-y-3 bg-[#0b1425]">
            <p className="text-white font-bold text-base">No Scheduled Interviews Yet</p>
            <p className="text-slate-400 text-xs max-w-md mx-auto">
              When recruiters review your job applications and schedule an AI technical interview or live room, it will appear here.
            </p>
            <Link
              href="/jobs"
              className="inline-block mt-2 py-2.5 px-5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs transition-all"
            >
              Browse Open Roles
            </Link>
          </div>
        ) : (
          interviews.map((item) => (
            <div
              key={item.id}
              className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6 hover:border-slate-700 transition-all bg-[#0b1425]"
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
                  <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
                    <Bot size={13} className="text-sky-400" />
                    <span>{item.jobTitle} • {item.interviewerName}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Link
                    href={item.meetingUrl}
                    className="py-3 px-6 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 font-bold text-white text-xs shadow-lg shadow-sky-500/20 transition-all flex items-center space-x-2"
                  >
                    <Play size={14} />
                    <span>Launch AI Interview Room</span>
                    <span className="font-mono">&rarr;</span>
                  </Link>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800/80 text-xs font-mono">
                <div className="p-3 rounded-xl bg-[#080e1b] border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">SCHEDULED TIME</span>
                  <span className="text-slate-200 font-bold">{item.scheduledAt}</span>
                </div>
                <div className="p-3 rounded-xl bg-[#080e1b] border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">TIMEZONE</span>
                  <span className="text-slate-200">{item.timezone}</span>
                </div>
                <div className="p-3 rounded-xl bg-[#080e1b] border border-slate-800">
                  <span className="text-slate-500 block text-[10px]">EVALUATION PROTOCOL</span>
                  <span className="text-emerald-400 font-bold">5-Question AI Rubric ✓</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
