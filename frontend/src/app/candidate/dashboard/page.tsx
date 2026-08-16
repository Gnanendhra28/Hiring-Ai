"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth/AuthContext";

interface ApplicationItem {
  id: string;
  jobTitle: string;
  companyName: string;
  appliedDate: string;
  currentStage: "Submitted" | "Screening" | "Assessment" | "Interview" | "Offer";
  stageIndex: number; // 0 to 4
  matchScore: number;
  statusText: string;
  statusBadgeColor: string;
  nextStep: string;
  nextStepUrl: string;
}

interface RecommendedJob {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  matchScore: number;
  matchedSkills: string[];
}

export default function CandidateDashboardPage() {
  const { user } = useAuth();

  // Mock initial applications for rich demonstration (will also integrate with live API)
  const [applications] = useState<ApplicationItem[]>([
    {
      id: "app-101",
      jobTitle: "Senior Frontend Architect",
      companyName: "Acme Cloud Corp",
      appliedDate: "Aug 12, 2026",
      currentStage: "Interview",
      stageIndex: 3,
      matchScore: 96,
      statusText: "Technical Interview Scheduled",
      statusBadgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
      nextStep: "Join Video Interview",
      nextStepUrl: "/candidate/interviews",
    },
    {
      id: "app-102",
      jobTitle: "Staff AI Systems Engineer",
      companyName: "Nexus Hiring AI",
      appliedDate: "Aug 14, 2026",
      currentStage: "Assessment",
      stageIndex: 2,
      matchScore: 92,
      statusText: "Coding Assessment Pending",
      statusBadgeColor: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30",
      nextStep: "Start Assessment",
      nextStepUrl: "/candidate/assessments",
    },
    {
      id: "app-103",
      jobTitle: "Lead Full Stack Developer",
      companyName: "Vortex Scale Labs",
      appliedDate: "Aug 15, 2026",
      currentStage: "Screening",
      stageIndex: 1,
      matchScore: 88,
      statusText: "Application Under Review",
      statusBadgeColor: "bg-sky-500/10 text-sky-400 border-sky-500/30",
      nextStep: "View Status",
      nextStepUrl: "/candidate/applications",
    },
  ]);

  const [recommendedJobs] = useState<RecommendedJob[]>([
    {
      id: "job-201",
      title: "Principal React & Next.js Engineer",
      company: "AuraHire Enterprise Systems",
      location: "Remote • San Francisco, CA",
      salary: "$180,000 - $220,000",
      matchScore: 98,
      matchedSkills: ["React 19", "Next.js App Router", "TypeScript", "Tailwind CSS"],
    },
    {
      id: "job-202",
      title: "Senior Full Stack Python/FastAPI Developer",
      company: "CloudScale AI Labs",
      location: "Hybrid • Bangalore, India",
      salary: "₹35,000,000 - ₹45,000,000",
      matchScore: 94,
      matchedSkills: ["FastAPI", "AsyncIO", "PostgreSQL RLS", "Vector Search"],
    },
  ]);

  const firstName = user?.full_name ? user.full_name.split(" ")[0] : "Candidate";

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* ------------------------------------------------ WELCOME HERO BANNER ------------------------------------------------ */}
      <div className="relative rounded-3xl glass-panel p-8 md:p-10 border border-slate-800 shadow-2xl overflow-hidden">
        <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
              <span>OVERVIEW &amp; JOB SEARCH WORKFLOW</span>
            </div>
            <h1 className="text-3xl md:text-4xl font-black text-white tracking-tight">
              Welcome back, <span className="text-gradient-cyan">{firstName}</span> 👋
            </h1>
            <p className="text-slate-300 text-sm leading-relaxed">
              Track your active job applications, complete skill assessments, and discover high-alignment positions backed by transparent AI evaluation.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Link
              href="/jobs"
              className="py-3 px-5 rounded-xl btn-shimmer font-bold text-white shadow-lg shadow-sky-500/20 text-xs text-center transition-all flex items-center justify-center space-x-2"
            >
              <span>Explore Jobs</span>
              <span className="font-mono">→</span>
            </Link>
            <Link
              href="/candidate/profile"
              className="py-3 px-5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-bold text-xs text-center transition-all"
            >
              Edit Profile
            </Link>
          </div>
        </div>

        {/* Profile Completeness Bar */}
        <div className="mt-8 pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center space-x-3">
            <span className="font-mono text-slate-400 uppercase">Profile Completeness:</span>
            <div className="w-48 h-2 rounded-full bg-slate-900 border border-slate-800 overflow-hidden">
              <div className="h-full bg-gradient-to-r from-sky-500 to-emerald-400 rounded-full w-[85%]" />
            </div>
            <span className="font-mono font-bold text-sky-400">85%</span>
          </div>
          <span className="text-slate-500">Add your latest project portfolio to reach 100% match accuracy.</span>
        </div>
      </div>

      {/* ------------------------------------------------ METRICS STRIP (4 CARDS) ------------------------------------------------ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Applications */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>ACTIVE APPLICATIONS</span>
            <span className="w-2 h-2 rounded-full bg-sky-400" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight">{applications.length}</div>
          <p className="text-xs text-slate-400">Applications submitted across positions</p>
        </div>

        {/* Pending Assessments */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>ASSESSMENTS PENDING</span>
            <span className="w-2 h-2 rounded-full bg-indigo-400" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight">1</div>
          <p className="text-xs text-slate-400">Coding challenge due in 2 days</p>
        </div>

        {/* Scheduled Interviews */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>INTERVIEWS SCHEDULED</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <div className="text-3xl font-black text-white tracking-tight">1</div>
          <p className="text-xs text-emerald-400 font-medium">Tomorrow at 2:00 PM IST</p>
        </div>

        {/* Avg Skill Alignment */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2 hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>AVG SKILL MATCH</span>
            <span className="text-xs text-emerald-400 font-bold">94%</span>
          </div>
          <div className="text-3xl font-black text-gradient-cyan tracking-tight">94%</div>
          <p className="text-xs text-slate-400">Evidence-backed vector match score</p>
        </div>
      </div>

      {/* ------------------------------------------------ APPLICATION STAGE TRACKER ------------------------------------------------ */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <h2 className="text-xl font-black text-white tracking-tight">Active Application Pipeline</h2>
            <p className="text-xs text-slate-400 mt-0.5">Real-time status updates and recruitment stage progress.</p>
          </div>
          <Link
            href="/candidate/applications"
            className="text-xs font-mono text-sky-400 hover:text-sky-300 font-bold hover:underline"
          >
            View All Applications →
          </Link>
        </div>

        <div className="space-y-6">
          {applications.map((app) => (
            <div key={app.id} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-5">
              {/* Job Info Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-3">
                    <h3 className="text-base font-bold text-white">{app.jobTitle}</h3>
                    <span className={`text-[10px] font-mono px-2.5 py-0.5 rounded-full border font-bold ${app.statusBadgeColor}`}>
                      {app.statusText}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex items-center space-x-3 font-mono">
                    <span>{app.companyName}</span>
                    <span>•</span>
                    <span>Applied: {app.appliedDate}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-[10px] font-mono uppercase text-slate-500">Skill Alignment</div>
                    <div className="text-sm font-black text-emerald-400 font-mono">{app.matchScore}% Match</div>
                  </div>
                  <Link
                    href={app.nextStepUrl}
                    className="py-2 px-4 rounded-xl btn-shimmer text-xs font-bold text-white shadow-md shadow-sky-500/10"
                  >
                    {app.nextStep}
                  </Link>
                </div>
              </div>

              {/* 5-Stage Visual Stepper */}
              <div className="pt-2">
                <div className="grid grid-cols-5 gap-2 text-center text-[10px] font-mono uppercase">
                  {["Submitted", "Screening", "Assessment", "Interview", "Offer"].map((stageName, idx) => {
                    const isCompleted = idx <= app.stageIndex;
                    const isCurrent = idx === app.stageIndex;
                    return (
                      <div key={stageName} className="space-y-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isCurrent
                              ? "bg-sky-400 shadow-lg shadow-sky-400/50 animate-pulse"
                              : isCompleted
                              ? "bg-emerald-500"
                              : "bg-slate-800"
                          }`}
                        />
                        <span className={isCompleted ? "text-slate-200 font-bold" : "text-slate-600"}>
                          {stageName}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------ RECOMMENDED JOBS GRID & UPCOMING EVENTS ------------------------------------------------ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recommended Jobs (Left 2 cols) */}
        <div className="lg:col-span-2 glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div>
              <h2 className="text-lg font-black text-white tracking-tight">Recommended Job Matches</h2>
              <p className="text-xs text-slate-400 mt-0.5">High-alignment opportunities matched to your skill profile.</p>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-sky-500/10 text-sky-400 border border-sky-500/20">
              AI MATCHED
            </span>
          </div>

          <div className="space-y-4">
            {recommendedJobs.map((job) => (
              <div key={job.id} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4 hover:border-slate-700 transition-all">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">{job.title}</h3>
                    <div className="text-xs text-slate-400 mt-0.5 font-mono">{job.company} • {job.location}</div>
                  </div>
                  <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                    {job.matchScore}% Match
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800/60">
                  <div className="flex flex-wrap gap-1.5">
                    {job.matchedSkills.map((skill) => (
                      <span key={skill} className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono text-slate-300">
                        {skill}
                      </span>
                    ))}
                  </div>
                  <Link
                    href={`/jobs`}
                    className="text-xs font-mono text-sky-400 font-bold hover:underline shrink-0 pl-2"
                  >
                    View Job →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Sidebar: Upcoming Events & Security Governance */}
        <div className="space-y-6">
          {/* Next Interview Widget */}
          <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
            <div className="text-xs font-mono uppercase text-slate-400 flex items-center justify-between">
              <span>UPCOMING INTERVIEW</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </div>

            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="text-sm font-bold text-white">Senior Frontend Architect</div>
              <div className="text-xs text-slate-400 font-mono">Acme Cloud Corp</div>
              <div className="text-xs text-sky-400 font-mono pt-1">Tomorrow, 2:00 PM - 3:00 PM IST</div>
            </div>

            <Link
              href="/candidate/interviews"
              className="block w-full py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-center text-xs font-bold text-slate-200 transition-colors"
            >
              Go to Interviews Room
            </Link>
          </div>

          {/* AI Governance Note */}
          <div className="p-6 rounded-3xl glass-panel border border-emerald-500/30 bg-emerald-950/20 space-y-3">
            <div className="flex items-center space-x-2 text-emerald-400 text-xs font-mono font-bold">
              <span>✓</span>
              <span>HUMAN DECISION GUARANTEE</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              AI evaluates skill evidence to present transparent match scores. All final advance, interview, and offer decisions are made exclusively by recruiters.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
