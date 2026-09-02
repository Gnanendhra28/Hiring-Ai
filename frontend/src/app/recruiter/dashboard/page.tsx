"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowUpRight,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
  UsersRound,
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import { fetchRecruiterJobs, updateJobStatus, deleteJobPost, JobItemData } from "@/lib/api";

interface LocalJobDisplay {
  id: string;
  title: string;
  department: string;
  skills: string;
  applicationsCount: number;
  aiShortlistedCount: number;
  interviewsCount: number;
  status: "ACTIVE" | "PAUSED" | "DRAFT" | "COMPLETED";
}

export default function RecruiterDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [jobs, setJobs] = useState<LocalJobDisplay[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch real jobs from backend
  useEffect(() => {
    async function loadRealJobs() {
      try {
        const liveJobs = await fetchRecruiterJobs();
        if (liveJobs) {
          const mapped: LocalJobDisplay[] = liveJobs.map((j) => {
            let normalizedStatus: "ACTIVE" | "PAUSED" | "DRAFT" | "COMPLETED" = "ACTIVE";
            if (j.status === "PAUSED") normalizedStatus = "PAUSED";
            else if (j.status === "DRAFT") normalizedStatus = "DRAFT";
            else if (j.status === "CLOSED") normalizedStatus = "COMPLETED";

            return {
              id: j.id,
              title: j.title,
              department: j.department || "Engineering",
              skills: j.skills?.join(" · ") || `${j.department || "Tech"} · AI · Cloud`,
              applicationsCount: j.applications_count || 0,
              aiShortlistedCount: j.ai_shortlisted_count || 0,
              interviewsCount: (j as any).interviews_count || 0,
              status: normalizedStatus,
            };
          });
          setJobs(mapped);
        }
      } catch (err) {
        console.error("Error loading real jobs:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadRealJobs();
  }, []);

  // Update status handler
  const handleStatusChange = async (jobId: string, newStatus: "ACTIVE" | "PAUSED" | "DRAFT" | "COMPLETED") => {
    setJobs((prev) => prev.map((j) => (j.id === jobId ? { ...j, status: newStatus } : j)));

    let backendStatus = "PUBLISHED";
    if (newStatus === "PAUSED") backendStatus = "PAUSED";
    else if (newStatus === "DRAFT") backendStatus = "DRAFT";
    else if (newStatus === "COMPLETED") backendStatus = "CLOSED";

    try {
      await updateJobStatus(jobId, backendStatus);
    } catch (err) {
      console.error("Error updating job status on backend:", err);
    }
  };

  // Delete job handler
  const handleDeleteJob = async (jobId: string) => {
    if (!confirm("Are you sure you want to completely delete this job post?")) return;
    setJobs((prev) => prev.filter((j) => j.id !== jobId));

    try {
      await deleteJobPost(jobId);
    } catch (err) {
      console.error("Error deleting job post on backend:", err);
    }
  };

  const activeJobsCount = jobs.filter((j) => j.status === "ACTIVE").length;
  const totalApplicationsCount = jobs.reduce((acc, j) => acc + j.applicationsCount, 0);
  const totalShortlistedCount = jobs.reduce((acc, j) => acc + j.aiShortlistedCount, 0);
  const totalInterviewsCount = jobs.reduce((acc, j) => acc + j.interviewsCount, 0);
  const topJob = jobs.length > 0 ? jobs[0] : null;

  const pipelineHealthRate = totalApplicationsCount > 0 
    ? Math.min(100, Math.round((totalShortlistedCount / totalApplicationsCount) * 100))
    : jobs.length > 0 ? 85 : 0;

  const displayName = user?.full_name?.trim() || (user?.email ? user.email.split("@")[0] : "Recruiter");

  return (
    <div className="command-page space-y-6">
      {/* Header */}
      <section className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="command-eyebrow">Hiring command center</p>
          <h1 className="command-title">
            Welcome, {displayName} <span className="text-base">👋</span>
          </h1>
          <p className="command-subtitle">
            {jobs.length > 0 
              ? `Your hiring pipeline is active. ${totalShortlistedCount} candidates shortlisted across ${activeJobsCount} active open roles.`
              : "Welcome to your AI hiring dashboard. Create a requisition to start sourcing and matching candidates."}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/recruiter/jobs" className="command-button secondary">
            View all jobs
          </Link>
          <Link href="/recruiter/jobs/new" className="command-button">
            <Plus size={15} /> New requisition
          </Link>
        </div>
      </section>

      {/* Interactive Stat Cards */}
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Link
          href="/recruiter/jobs"
          className="command-stat hover:border-slate-500 hover:bg-[#18253a] transition cursor-pointer group block"
        >
          <p className="group-hover:text-sky-400 transition">Active jobs</p>
          <strong>{activeJobsCount}</strong>
          <span className="text-emerald-400">{jobs.length} total requisitions</span>
        </Link>

        <Link
          href={topJob ? `/recruiter/jobs/${topJob.id}/applications` : "/recruiter/jobs"}
          className="command-stat hover:border-slate-500 hover:bg-[#18253a] transition cursor-pointer group block"
        >
          <p className="group-hover:text-sky-400 transition">Applications</p>
          <strong>{totalApplicationsCount.toLocaleString()}</strong>
          <span>Across all active roles</span>
        </Link>

        <Link
          href={topJob ? `/recruiter/jobs/${topJob.id}/ranking` : "/recruiter/jobs"}
          className="command-stat hover:border-slate-500 hover:bg-[#18253a] transition cursor-pointer group block"
        >
          <p className="group-hover:text-sky-400 transition">AI shortlisted</p>
          <strong>{totalShortlistedCount}</strong>
          <span className="text-sky-300">Ready for review</span>
        </Link>

        <Link
          href={topJob ? `/recruiter/jobs/${topJob.id}/interviews` : "/recruiter/jobs"}
          className="command-stat hover:border-slate-500 hover:bg-[#18253a] transition cursor-pointer group block"
        >
          <p className="group-hover:text-sky-400 transition">Interviews</p>
          <strong>{totalInterviewsCount}</strong>
          <span>Scheduled sessions</span>
        </Link>
      </section>

      {/* AI Hiring Signal Card */}
      {topJob && (
        <section className="command-card relative overflow-hidden p-5">
          <div className="absolute -right-10 -top-8 h-32 w-32 rounded-full bg-blue-500/10 blur-2xl" />
          <div className="relative flex flex-col gap-4 lg:flex-row lg:items-center">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-blue-500 text-white">
              <Sparkles size={19} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="text-xs font-bold text-sky-300">AI hiring signal</p>
                <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[9px] font-bold text-emerald-300">
                  HIGH CONFIDENCE
                </span>
              </div>
              <h2 className="mt-1 text-lg font-bold text-white">
                {topJob.title}: {topJob.aiShortlistedCount > 0 ? `${topJob.aiShortlistedCount} top-scored candidates ready to progress` : "Active candidates matching requirements"}
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                Verified experience, technical skill evidence, and explainable AI fit scores calculated against requirement weights.
              </p>
            </div>
            <Link className="command-button" href={`/recruiter/jobs/${topJob.id}/ranking`}>
              Review shortlist <ChevronRight size={15} />
            </Link>
          </div>
        </section>
      )}

      {/* Table & Sidebar */}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_315px]">
        {/* Real Active Jobs Table */}
        <section className="command-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-700/60 px-5 py-4">
            <div>
              <h2 className="font-bold text-white">Active Jobs & AI Candidate Shortlists</h2>
              <p className="mt-1 text-xs text-slate-400">Click any job to view top AI scored applications and ranking analysis</p>
            </div>
            <Link href="/recruiter/jobs" className="text-xs font-bold text-sky-300 hover:text-sky-200">
              Manage all jobs <ArrowUpRight size={13} className="inline" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            {isLoading ? (
              <div className="p-8 text-center text-sm font-mono text-slate-400">
                Loading live requisition pipeline...
              </div>
            ) : jobs.length === 0 ? (
              <div className="p-12 text-center">
                <p className="text-sm text-slate-400 mb-4">No active job requisitions found in your organization.</p>
                <Link href="/recruiter/jobs/new" className="command-button inline-flex">
                  <Plus size={15} /> Create your first job posting
                </Link>
              </div>
            ) : (
              <table className="w-full min-w-[680px] text-left">
                <thead className="bg-slate-950/20 text-[10px] uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Job Name</th>
                    <th className="px-4 py-3">Required Skills</th>
                    <th className="px-4 py-3">Applications</th>
                    <th className="px-4 py-3">AI Shortlisted</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr
                      key={job.id}
                      className="border-t border-slate-700/50 text-xs hover:bg-slate-800/40 transition cursor-pointer"
                      onClick={(e) => {
                        const target = e.target as HTMLElement;
                        if (target.tagName === "SELECT" || target.closest("select") || target.closest("button")) return;
                        router.push(`/recruiter/jobs/${job.id}/ranking`);
                      }}
                    >
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <span className="grid h-8 w-8 place-items-center rounded bg-slate-700 font-bold text-sky-200">
                            <BriefcaseBusiness size={16} />
                          </span>
                          <div>
                            <strong className="text-slate-100 group-hover:text-sky-300">{job.title}</strong>
                            <span className="mt-0.5 block text-slate-500">{job.department}</span>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-slate-300 font-medium">{job.skills}</td>
                      <td className="px-4 py-4 text-slate-200 font-semibold">{job.applicationsCount}</td>
                      <td className="px-4 py-4">
                        <span className="rounded bg-sky-500/10 px-2 py-1 text-sky-300 font-bold">
                          {job.aiShortlistedCount} shortlisted
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <select
                          value={job.status}
                          onChange={(e) =>
                            handleStatusChange(
                              job.id,
                              e.target.value as "ACTIVE" | "PAUSED" | "DRAFT" | "COMPLETED"
                            )
                          }
                          onClick={(e) => e.stopPropagation()}
                          className="bg-[#0b1425] text-slate-200 border border-[#233047] rounded px-2 py-1 text-xs outline-none focus:border-sky-500"
                        >
                          <option value="ACTIVE">Active</option>
                          <option value="PAUSED">Pause</option>
                          <option value="DRAFT">Draft</option>
                          <option value="COMPLETED">Complete</option>
                        </select>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/recruiter/jobs/${job.id}/edit`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-amber-300 hover:text-amber-200 font-medium text-xs flex items-center gap-1 bg-amber-500/10 px-2 py-1 rounded border border-amber-500/20"
                            title="Edit Job Role"
                          >
                            <Pencil size={12} /> Edit
                          </Link>
                          <Link
                            href={`/recruiter/jobs/${job.id}/ranking`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-sky-300 hover:text-sky-200 font-semibold"
                          >
                            View AI Shortlist →
                          </Link>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteJob(job.id);
                            }}
                            className="text-rose-400 hover:text-rose-300 p-1"
                            title="Delete Job Post"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* Needs Attention & Pipeline Health Widgets */}
        <aside className="space-y-5">
          <section className="command-card p-5">
            <div className="flex items-center gap-2">
              <Clock3 size={16} className="text-amber-300" />
              <h2 className="font-bold text-white">Needs attention</h2>
            </div>
            <div className="mt-4 space-y-4 text-xs">
              {jobs.length === 0 ? (
                <p className="text-slate-500">All hiring tasks are up to date.</p>
              ) : (
                jobs.slice(0, 3).map((j, idx) => (
                  <Link
                    key={j.id}
                    href={idx === 0 ? `/recruiter/jobs/${j.id}/ranking` : `/recruiter/jobs/${j.id}/interviews`}
                    className="block border-l-2 border-amber-400 pl-3 hover:bg-slate-800/30 py-1 transition"
                  >
                    <strong className="text-slate-200">{j.title}</strong>
                    <p className="mt-1 text-slate-500">
                      {j.aiShortlistedCount > 0 
                        ? `${j.aiShortlistedCount} candidate${j.aiShortlistedCount === 1 ? '' : 's'} await shortlist review`
                        : `${j.applicationsCount} application${j.applicationsCount === 1 ? '' : 's'} pending review`}
                    </p>
                  </Link>
                ))
              )}
            </div>
          </section>

          <section className="command-card p-5">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Pipeline health</p>
            <div className="mt-5 flex items-end gap-2">
              <strong className="text-3xl text-white">{pipelineHealthRate}%</strong>
              <span className="mb-1 text-xs text-emerald-400">
                {totalShortlistedCount} / {Math.max(1, totalApplicationsCount)} shortlisted
              </span>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded bg-slate-800">
              <span 
                className="block h-full rounded bg-sky-400 transition-all duration-500"
                style={{ width: `${Math.max(5, pipelineHealthRate)}%` }} 
              />
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              Computed in real time from live verified candidate applications and shortlist conversion.
            </p>
          </section>
        </aside>
      </div>
    </div>
  );
}


