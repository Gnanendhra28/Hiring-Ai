"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BriefcaseBusiness,
  CheckCircle2,
  FileCheck,
  Pencil,
  Plus,
  ShieldCheck,
  Sparkles,
  Trash2,
  UserCheck,
  UserPlus,
} from "lucide-react";
import {
  fetchRecruiterJobs,
  updateJobStatus,
  deleteJobPost,
  deleteJobAdmin,
  fetchPendingJobsAdmin,
  fetchAllJobsAdmin,
  verifyJobAdmin,
  JobItemData,
} from "@/lib/api";

interface LocalJobDisplay {
  id: string;
  title: string;
  department: string;
  skills: string;
  applicationsCount: number;
  aiShortlistedCount: number;
  status: "ACTIVE" | "PAUSED" | "DRAFT" | "COMPLETED";
}

export default function AdminJobsApprovalPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<LocalJobDisplay[]>([]);
  const [pendingJobs, setPendingJobs] = useState<JobItemData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [verifyingJobId, setVerifyingJobId] = useState<string | null>(null);

  useEffect(() => {
    async function loadJobsData() {
      try {
        const [liveJobs, pendingJbs] = await Promise.all([
          fetchAllJobsAdmin().catch(() => []),
          fetchPendingJobsAdmin().catch(() => []),
        ]);

        if (liveJobs && liveJobs.length > 0) {
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
              status: normalizedStatus,
            };
          });
          setJobs(mapped);
        } else {
          setJobs([]);
        }

        setPendingJobs(pendingJbs || []);
      } catch (err) {
        console.error("Error loading jobs approval data:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadJobsData();
  }, []);

  const handleStatusChange = async (
    jobId: string,
    newStatus: "ACTIVE" | "PAUSED" | "DRAFT" | "COMPLETED"
  ) => {
    const backendStatus =
      newStatus === "ACTIVE"
        ? "PUBLISHED"
        : newStatus === "COMPLETED"
        ? "CLOSED"
        : newStatus;

    setJobs((prevJobs) =>
      prevJobs.map((j) => (j.id === jobId ? { ...j, status: newStatus } : j))
    );

    try {
      await updateJobStatus(jobId, backendStatus);
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm("Are you sure you want to completely delete this job posting from the portal?")) return;
    setJobs((prev) => prev.filter((j) => j.id !== jobId));
    try {
      await deleteJobAdmin(jobId);
    } catch (err) {
      console.error("Failed to delete job:", err);
    }
  };

  const handleVerifyJob = async (jobId: string, action: "APPROVE" | "REJECT") => {
    setVerifyingJobId(jobId);
    try {
      const ok = await verifyJobAdmin(jobId, action);
      if (ok) {
        setPendingJobs((prev) => prev.filter((j) => j.id !== jobId));
      }
    } catch (err) {
      console.error("Error verifying job post:", err);
    } finally {
      setVerifyingJobId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-wider flex items-center gap-1">
                <FileCheck size={12} /> Jobs Approval Portal
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Approve Job Postings Created by Employees
            </h1>
            <p className="text-slate-400 text-xs md:text-sm max-w-2xl">
              Inspect and verify job requisitions submitted by recruiter organizations across the platform before public publication.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/employers")}
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <UserCheck size={14} /> Approve Employees &rarr;
            </button>
            <button
              onClick={() => router.push("/admin/add-admin")}
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <UserPlus size={14} /> Add Admin
            </button>
          </div>
        </div>

        {/* Section 1: Pending Job Posts Verification Queue */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <FileCheck className="text-amber-400" size={20} />
              <h2 className="text-lg font-bold text-white">Pending Job Requisitions Queue</h2>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {pendingJobs.length} Awaiting Verification
            </span>
          </div>

          {pendingJobs.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
              <CheckCircle2 className="mx-auto text-slate-600" size={36} />
              <div className="text-sm font-semibold text-slate-300">No Job Requisitions Awaiting Verification</div>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                All submitted recruiter job postings have been reviewed and approved for platform publication.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                  <tr>
                    <th className="px-5 py-3">Job Title & Role</th>
                    <th className="px-5 py-3">Department & Location</th>
                    <th className="px-5 py-3">Employment Type</th>
                    <th className="px-5 py-3">Submitted Date</th>
                    <th className="px-5 py-3 text-right">Job Verification Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b263b] text-slate-200">
                  {pendingJobs.map((j) => (
                    <tr key={j.id} className="hover:bg-[#18253a]/50 transition">
                      <td className="px-5 py-4 font-bold text-white text-sm">{j.title}</td>
                      <td className="px-5 py-4 text-slate-300">{j.department || "Engineering"} &bull; {j.location || "Remote"}</td>
                      <td className="px-5 py-4 text-slate-400">{j.employment_type || "FULL_TIME"}</td>
                      <td className="px-5 py-4 text-slate-400">{new Date(j.created_at).toLocaleDateString()}</td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleVerifyJob(j.id, "APPROVE")}
                            disabled={verifyingJobId === j.id}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center gap-1 shadow transition"
                          >
                            <CheckCircle2 size={13} /> {verifyingJobId === j.id ? "Approving..." : "Approve & Publish Job"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleVerifyJob(j.id, "REJECT")}
                            disabled={verifyingJobId === j.id}
                            className="px-2.5 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded text-xs font-medium border border-rose-500/20 transition"
                          >
                            Reject Job
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section 2: Verified Platform Job Postings Workspace */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <BriefcaseBusiness className="text-sky-400" size={20} /> Verified & Active Platform Job Postings
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                <tr>
                  <th className="px-5 py-3">Job Role</th>
                  <th className="px-5 py-3">Department</th>
                  <th className="px-5 py-3">Skills Required</th>
                  <th className="px-5 py-3">Applications</th>
                  <th className="px-5 py-3">AI Shortlisted</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b263b] text-slate-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-[#18253a]/50 transition">
                    <td className="px-5 py-4 font-bold text-white text-sm">{job.title}</td>
                    <td className="px-5 py-4 text-slate-300">{job.department}</td>
                    <td className="px-5 py-4 text-slate-400">{job.skills}</td>
                    <td className="px-5 py-4 font-bold text-slate-200">{job.applicationsCount}</td>
                    <td className="px-5 py-4 font-bold text-sky-400">{job.aiShortlistedCount}</td>
                    <td className="px-5 py-4">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                        job.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : job.status === "PAUSED"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                          : job.status === "DRAFT"
                          ? "bg-slate-500/10 text-slate-400 border-slate-500/20"
                          : "bg-red-500/10 text-red-400 border-red-500/20"
                      }`}>
                        {job.status === "ACTIVE" ? "Active" : job.status === "PAUSED" ? "Paused" : job.status === "DRAFT" ? "Draft" : "Closed"}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/recruiter/jobs/${job.id}/edit`}
                          className="text-amber-300 hover:text-amber-200 font-medium text-xs flex items-center gap-1 bg-amber-500/10 px-2 py-1 rounded border border-amber-500/20"
                          title="Edit Job Role"
                        >
                          <Pencil size={12} /> Edit
                        </Link>
                        <Link
                          href={`/recruiter/jobs/${job.id}/ranking`}
                          className="text-sky-300 hover:text-sky-200 font-semibold"
                        >
                          View AI Shortlist &rarr;
                        </Link>
                        <button
                          type="button"
                          onClick={() => handleDeleteJob(job.id)}
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
          </div>
        </div>
      </div>
    </div>
  );
}
