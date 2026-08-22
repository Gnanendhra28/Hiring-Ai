"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BriefcaseBusiness,
  CheckCircle2,
  FileCheck,
  MoreVertical,
  Pencil,
  Sparkles,
  Trash2,
  UserCheck,
  UserPlus,
} from "lucide-react";
import {
  fetchRecruiterJobs,
  updateJobStatus,
  deleteJobAdmin,
  batchDeleteJobsAdmin,
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
  created_at?: string;
}

export default function AdminJobsApprovalPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<LocalJobDisplay[]>([]);
  const [pendingJobs, setPendingJobs] = useState<JobItemData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [verifyingJobId, setVerifyingJobId] = useState<string | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);
  const [isDeletingBatch, setIsDeletingBatch] = useState(false);

  useEffect(() => {
    async function loadJobsData() {
      try {
        const [liveJobs, pendingJbs] = await Promise.all([
          fetchAllJobsAdmin().catch(() => []),
          fetchPendingJobsAdmin().catch(() => []),
        ]);

        if (liveJobs && liveJobs.length > 0) {
          // Sort recently posted jobs at top (descending by created_at)
          const sortedJobs = [...liveJobs].sort((a, b) => {
            const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
            const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
            return timeB - timeA;
          });

          const mapped: LocalJobDisplay[] = sortedJobs.map((j) => {
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
              created_at: j.created_at,
            };
          });
          setJobs(mapped);
        } else {
          setJobs([]);
        }

        if (pendingJbs && pendingJbs.length > 0) {
          const sortedPending = [...pendingJbs].sort((a, b) => {
            const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
            const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
            return timeB - timeA;
          });
          setPendingJobs(sortedPending);
        } else {
          setPendingJobs([]);
        }
      } catch (err) {
        console.error("Error loading jobs approval data:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadJobsData();
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest(".dropdown-container")) {
        setOpenDropdownId(null);
      }
    };
    window.addEventListener("click", handleOutsideClick);
    return () => window.removeEventListener("click", handleOutsideClick);
  }, []);

  const handleDeleteJob = async (jobId: string) => {
    setOpenDropdownId(null);
    if (!confirm("Are you sure you want to completely delete this job posting from the portal?")) return;
    setJobs((prev) => prev.filter((j) => j.id !== jobId));
    setSelectedJobIds((prev) => prev.filter((id) => id !== jobId));
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

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedJobIds(jobs.map((j) => j.id));
    } else {
      setSelectedJobIds([]);
    }
  };

  const handleSelectOne = (jobId: string) => {
    setSelectedJobIds((prev) =>
      prev.includes(jobId) ? prev.filter((id) => id !== jobId) : [...prev, jobId]
    );
  };

  const handleBatchDelete = async () => {
    if (selectedJobIds.length === 0) return;
    if (
      !confirm(
        `Are you sure you want to permanently delete all ${selectedJobIds.length} selected jobs from the portal?`
      )
    )
      return;

    const idsToDelete = [...selectedJobIds];
    setIsDeletingBatch(true);

    setJobs((prev) => prev.filter((j) => !idsToDelete.includes(j.id)));
    setSelectedJobIds([]);

    try {
      await batchDeleteJobsAdmin(idsToDelete);
    } catch (err) {
      console.error("Failed to batch delete jobs:", err);
    } finally {
      setIsDeletingBatch(false);
    }
  };

  const allSelected = jobs.length > 0 && selectedJobIds.length === jobs.length;

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
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <BriefcaseBusiness className="text-sky-400" size={20} /> Verified & Active Platform Job Postings ({jobs.length})
            </h2>

            {/* Bulk Actions */}
            {selectedJobIds.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400 font-medium">
                  {selectedJobIds.length} job{selectedJobIds.length > 1 ? "s" : ""} selected
                </span>
                <button
                  onClick={handleBatchDelete}
                  disabled={isDeletingBatch}
                  className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow"
                >
                  <Trash2 size={13} /> {isDeletingBatch ? "Deleting..." : `Delete Selected (${selectedJobIds.length})`}
                </button>
              </div>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                <tr>
                  <th className="px-4 py-3 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={handleSelectAll}
                      className="rounded bg-[#0b1425] border-[#233047] text-sky-500 focus:ring-0 cursor-pointer"
                    />
                  </th>
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
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-500 text-xs">
                      No platform job postings found.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => {
                    const isSelected = selectedJobIds.includes(job.id);
                    const isMenuOpen = openDropdownId === job.id;

                    return (
                      <tr
                        key={job.id}
                        className={`transition ${
                          isSelected ? "bg-sky-500/10" : "hover:bg-[#18253a]/50"
                        }`}
                      >
                        <td className="px-4 py-4 text-center">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleSelectOne(job.id)}
                            className="rounded bg-[#0b1425] border-[#233047] text-sky-500 focus:ring-0 cursor-pointer"
                          />
                        </td>
                        <td className="px-5 py-4 font-bold text-white text-sm">{job.title}</td>
                        <td className="px-5 py-4 text-slate-300">{job.department}</td>
                        <td className="px-5 py-4 text-slate-400">{job.skills}</td>
                        <td className="px-5 py-4 font-bold text-slate-200">{job.applicationsCount}</td>
                        <td className="px-5 py-4 font-bold text-sky-400">{job.aiShortlistedCount}</td>
                        <td className="px-5 py-4">
                          <span
                            className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                              job.status === "ACTIVE"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                : job.status === "PAUSED"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                : job.status === "DRAFT"
                                ? "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                : "bg-red-500/10 text-red-400 border-red-500/20"
                            }`}
                          >
                            {job.status === "ACTIVE"
                              ? "Active"
                              : job.status === "PAUSED"
                              ? "Paused"
                              : job.status === "DRAFT"
                              ? "Draft"
                              : "Closed"}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right relative dropdown-container">
                          {/* Three Dots Menu Button */}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenDropdownId(isMenuOpen ? null : job.id);
                            }}
                            className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition"
                            title="Actions menu"
                          >
                            <MoreVertical size={16} />
                          </button>

                          {/* Action Dropdown Popup */}
                          {isMenuOpen && (
                            <div className="absolute right-5 top-12 z-50 w-44 bg-[#0d1627] border border-[#233047] rounded-xl shadow-2xl py-1 text-left">
                              <Link
                                href={`/recruiter/jobs/${job.id}/edit`}
                                className="w-full px-3 py-2 text-xs text-amber-300 hover:bg-slate-800/80 flex items-center gap-2 transition"
                              >
                                <Pencil size={13} /> Edit Job
                              </Link>
                              <Link
                                href={`/recruiter/jobs/${job.id}/ranking`}
                                className="w-full px-3 py-2 text-xs text-sky-300 hover:bg-slate-800/80 flex items-center gap-2 transition"
                              >
                                <Sparkles size={13} /> View AI Shortlist
                              </Link>
                              <div className="border-t border-slate-800 my-1"></div>
                              <button
                                type="button"
                                onClick={() => handleDeleteJob(job.id)}
                                className="w-full px-3 py-2 text-xs text-rose-400 hover:bg-rose-500/10 flex items-center gap-2 transition"
                              >
                                <Trash2 size={13} /> Delete Job
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
