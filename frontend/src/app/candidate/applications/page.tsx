"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Bookmark,
  Briefcase,
  CheckCircle2,
  Clock,
  FileCheck,
  MapPin,
  Sparkles,
  Trash2,
  XCircle,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

type TabType = "all" | "saved" | "shortlisted" | "interviews" | "closed";

interface RealApplicationRecord {
  id: string;
  jobId: string;
  jobTitle: string;
  department: string;
  location: string;
  salary?: string;
  submittedAt: string;
  status: string;
  closingDateStr?: string | null;
  isJobClosed?: boolean;
}

export default function CandidateApplicationsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("all");
  const [applications, setApplications] = useState<RealApplicationRecord[]>([]);
  const [savedJobs, setSavedJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Load real applications and saved jobs from PostgreSQL API
  const loadData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Candidate Real Applications from DB
      const resApps = await apiFetch("/api/v1/candidate/applications");
      if (resApps.ok) {
        const rawApps = await resApps.json();

        // 2. Fetch Job Details for each application
        const formattedApps = await Promise.all(
          rawApps.map(async (a: any) => {
            let jobInfo: any = {};
            try {
              const resJob = await apiFetch(`/api/v1/jobs/${a.job_id}`);
              if (resJob.ok) {
                jobInfo = await resJob.json();
              }
            } catch (err) {
              console.error("Error fetching job info for application:", err);
            }

            return {
              id: a.id,
              jobId: a.job_id,
              jobTitle: jobInfo.title || "Job Requisition",
              department: jobInfo.department || "Enterprise Requisition",
              location: jobInfo.location || "Remote",
              salary: jobInfo.salary || "₹ Competitive Package",
              submittedAt: new Date(a.submitted_at || Date.now()).toLocaleDateString(
                "en-US",
                {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                }
              ),
              status: a.status || "SUBMITTED",
            };
          })
        );

        setApplications(formattedApps);
      }

      // 3. Fetch Candidate Saved Jobs from local storage / API
      const savedIdsStr = localStorage.getItem("hiring_ai_saved_job_ids") || "[]";
      const savedIds: string[] = JSON.parse(savedIdsStr);

      if (savedIds.length > 0) {
        const savedJobsDetails = await Promise.all(
          savedIds.map(async (id: string) => {
            try {
              const res = await apiFetch(`/api/v1/jobs/${id}`);
              if (res.ok) return await res.json();
            } catch (e) {
              console.error("Error fetching saved job:", e);
            }
            return null;
          })
        );
        setSavedJobs(savedJobsDetails.filter(Boolean));
      } else {
        setSavedJobs([]);
      }
    } catch (err) {
      console.error("Error loading candidate applications & saved jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Action: Close / Withdraw Application
  const handleCloseApplication = async (appId: string) => {
    try {
      const res = await apiFetch(`/api/v1/candidate/applications/${appId}/close`, {
        method: "PATCH",
      });
      if (res.ok) {
        setActionMessage("Application has been closed/withdrawn.");
        loadData();
        setTimeout(() => setActionMessage(null), 3000);
      }
    } catch (err) {
      console.error("Error closing application:", err);
    }
  };

  // Action: Remove Saved Job
  const handleRemoveSavedJob = (jobId: string) => {
    const savedIdsStr = localStorage.getItem("hiring_ai_saved_job_ids") || "[]";
    const savedIds: string[] = JSON.parse(savedIdsStr);
    const updated = savedIds.filter((id) => id !== jobId);
    localStorage.setItem("hiring_ai_saved_job_ids", JSON.stringify(updated));
    setSavedJobs((prev) => prev.filter((j) => j.id !== jobId && j.slug !== jobId));
  };

  // Tab Filtering Logic
  const getFilteredList = () => {
    if (activeTab === "shortlisted") {
      return applications.filter(
        (a) => a.status === "SHORTLISTED" || a.status.toLowerCase().includes("shortlist")
      );
    }
    if (activeTab === "interviews") {
      return applications.filter(
        (a) =>
          a.status === "INTERVIEW" ||
          a.status.toLowerCase().includes("interview") ||
          a.status === "ASSESSMENT"
      );
    }
    if (activeTab === "closed") {
      return applications.filter(
        (a) =>
          a.status === "WITHDRAWN" ||
          a.status === "CLOSED" ||
          a.status === "REJECTED"
      );
    }
    return applications;
  };

  const filteredApps = getFilteredList();

  // Helper badge color renderer
  const renderStatusBadge = (status: string) => {
    const sUpper = status.toUpperCase();
    if (sUpper.includes("SHORTLIST")) {
      return (
        <span className="px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs font-bold flex items-center gap-1.5">
          🎯 Shortlisted
        </span>
      );
    }
    if (sUpper.includes("INTERVIEW") || sUpper.includes("ASSESSMENT")) {
      return (
        <span className="px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800 text-indigo-300 text-xs font-bold flex items-center gap-1.5">
          📅 Interview Scheduled
        </span>
      );
    }
    if (sUpper.includes("WITHDRAWN") || sUpper.includes("CLOSED") || sUpper.includes("REJECT")) {
      return (
        <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-400 text-xs font-bold flex items-center gap-1.5">
          🔒 Closed
        </span>
      );
    }
    return (
      <span className="px-3 py-1 rounded-full bg-blue-950/80 border border-blue-800 text-blue-300 text-xs font-bold flex items-center gap-1.5">
        <CheckCircle2 size={13} /> Submitted
      </span>
    );
  };

  return (
    <div className="h-page space-y-6 text-slate-100 font-sans">
      {/* Header */}
      <section className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-indigo-400">
            Candidate Application Hub
          </p>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            My Applications &amp; Saved Jobs
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-1">
            Track real applications, view shortlisted positions, manage interview schedules, and inspect saved jobs.
          </p>
        </div>
        <Link
          href="/jobs"
          className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all flex items-center gap-1.5"
        >
          Browse All Openings &rarr;
        </Link>
      </section>

      {actionMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-bold">
          {actionMessage}
        </div>
      )}

      {/* 5 Distinct Feature Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("all")}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "all"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
          }`}
        >
          <FileCheck size={14} /> All Applications ({applications.length})
        </button>

        <button
          onClick={() => setActiveTab("saved")}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "saved"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
          }`}
        >
          <Bookmark size={14} /> Saved Jobs ({savedJobs.length})
        </button>

        <button
          onClick={() => setActiveTab("shortlisted")}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "shortlisted"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
          }`}
        >
          🎯 Shortlisted (
          {
            applications.filter(
              (a) => a.status === "SHORTLISTED" || a.status.toLowerCase().includes("shortlist")
            ).length
          }
          )
        </button>

        <button
          onClick={() => setActiveTab("interviews")}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "interviews"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
          }`}
        >
          📅 Interviews (
          {
            applications.filter(
              (a) =>
                a.status === "INTERVIEW" ||
                a.status.toLowerCase().includes("interview") ||
                a.status === "ASSESSMENT"
            ).length
          }
          )
        </button>

        <button
          onClick={() => setActiveTab("closed")}
          className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "closed"
              ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
              : "bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800"
          }`}
        >
          🔒 Closed (
          {
            applications.filter(
              (a) =>
                a.status === "WITHDRAWN" ||
                a.status === "CLOSED" ||
                a.status === "REJECTED"
            ).length
          }
          )
        </button>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 font-semibold animate-pulse">
          Loading candidate data from database...
        </div>
      ) : activeTab === "saved" ? (
        /* SAVED JOBS TAB CONTENT */
        <div className="space-y-4">
          {savedJobs.length === 0 ? (
            <div className="p-12 rounded-2xl border border-slate-800 bg-slate-900 text-center space-y-3">
              <Bookmark size={32} className="mx-auto text-slate-500" />
              <h3 className="text-base font-bold text-white">No Saved Jobs Yet</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Bookmark job postings from the job directory to save positions you want to review and apply for later.
              </p>
              <Link
                href="/jobs"
                className="inline-block px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all"
              >
                Browse Job Directory
              </Link>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {savedJobs.map((job) => (
                <div
                  key={job.id || job.slug}
                  className="p-6 rounded-2xl border border-slate-800 bg-slate-900 space-y-4 shadow-xl hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-400">
                      {job.department || "Enterprise Requisition"}
                    </span>
                    <h3 className="text-lg font-bold text-white">{job.title}</h3>
                    <p className="text-xs text-slate-300 flex items-center gap-3">
                      <span>📍 {job.location || "Remote"}</span>
                      <span>💼 {job.employment_type || "Full-time"}</span>
                    </p>
                    {job.salary && (
                      <p className="text-xs font-semibold text-emerald-400 pt-1">
                        💰 {job.salary}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-800 pt-4 gap-2">
                    <button
                      onClick={() => handleRemoveSavedJob(job.id || job.slug)}
                      className="px-3.5 py-2 rounded-xl border border-slate-800 bg-slate-950 text-slate-400 hover:text-rose-400 text-xs font-bold flex items-center gap-1.5 transition-all"
                    >
                      <Trash2 size={14} /> Remove
                    </button>

                    <Link
                      href={`/jobs/${job.slug || job.id}`}
                      className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
                    >
                      Apply Now &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* APPLICATIONS TABS CONTENT (ALL / SHORTLISTED / INTERVIEWS / CLOSED) */
        <div className="space-y-4">
          {filteredApps.length === 0 ? (
            <div className="p-12 rounded-2xl border border-slate-800 bg-slate-900 text-center space-y-3">
              <FileCheck size={32} className="mx-auto text-slate-500" />
              <h3 className="text-base font-bold text-white">No Applications in &lsquo;{activeTab}&rsquo;</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                {activeTab === "all"
                  ? "You have not submitted any job applications yet. Browse open roles and apply!"
                  : activeTab === "shortlisted"
                  ? "None of your current applications have been marked as shortlisted by recruiters yet."
                  : activeTab === "interviews"
                  ? "No interview sessions scheduled for your applications yet."
                  : "No closed or withdrawn applications."}
              </p>
              <Link
                href="/jobs"
                className="inline-block px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all"
              >
                Explore Open Positions
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredApps.map((app) => {
                const isClosedApp =
                  app.status === "WITHDRAWN" ||
                  app.status === "CLOSED" ||
                  app.status === "REJECTED";

                return (
                  <div
                    key={app.id}
                    className="p-6 rounded-2xl border border-slate-800 bg-slate-900 space-y-4 shadow-xl hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
                  >
                    <div className="space-y-2 max-w-xl">
                      <div className="flex items-center gap-3">
                        {renderStatusBadge(app.status)}
                        <span className="text-xs text-slate-400 font-medium">
                          Submitted on {app.submittedAt}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-white">{app.jobTitle}</h3>

                      <p className="text-xs text-slate-300 flex flex-wrap items-center gap-3 font-medium">
                        <span>🏢 {app.department}</span>
                        <span>📍 {app.location}</span>
                        {app.salary && <span className="text-emerald-400">💰 {app.salary}</span>}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3 shrink-0 border-t md:border-t-0 border-slate-800 pt-4 md:pt-0">
                      <Link
                        href={`/jobs/${app.jobId}`}
                        className="px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-950 text-slate-300 hover:text-white text-xs font-bold transition-all flex items-center gap-1.5"
                      >
                        View Position <ArrowUpRight size={14} />
                      </Link>

                      {!isClosedApp && (
                        <button
                          onClick={() => handleCloseApplication(app.id)}
                          className="px-4 py-2.5 rounded-xl border border-rose-900/60 bg-rose-950/40 text-rose-300 hover:bg-rose-900/40 text-xs font-bold transition-all flex items-center gap-1.5"
                        >
                          <XCircle size={14} /> Close Application
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
