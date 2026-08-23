"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { CheckCircle2, Clock3, FileCheck, Pencil, Plus, Send, Trash2 } from "lucide-react";
import {
  fetchRecruiterJobs,
  updateJobStatus,
  submitJobForAdminApproval,
  deleteJobPost,
  JobItemData,
} from "@/lib/api";

export default function JobWorkspaceListPage() {
  const [jobs, setJobs] = useState<JobItemData[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [submittingJobId, setSubmittingJobId] = useState<string | null>(null);
  const [alertMsg, setAlertMsg] = useState<string | null>(null);

  const loadJobs = async () => {
    try {
      const liveJobs = await fetchRecruiterJobs();
      setJobs(liveJobs || []);
    } catch (err) {
      console.error("Failed to load live jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleStatusChange = async (jobId: string, newStatus: string) => {
    setJobs((prev) =>
      prev.map((j) => (j.id === jobId ? { ...j, status: newStatus as any } : j))
    );
    try {
      await updateJobStatus(jobId, newStatus);
    } catch (err) {
      console.error("Failed to update status on backend:", err);
    }
  };

  const handleSendToAdmin = async (jobId: string, title: string) => {
    setSubmittingJobId(jobId);
    setJobs((prev) =>
      prev.map((j) =>
        j.id === jobId ? { ...j, verification_status: "PENDING_VERIFICATION" } : j
      )
    );
    try {
      await submitJobForAdminApproval(jobId);
      setAlertMsg(`Job requisition "${title}" has been submitted to Platform Admin for approval.`);
      setTimeout(() => setAlertMsg(null), 5000);
    } catch (err) {
      console.error("Failed to submit job for admin approval:", err);
    } finally {
      setSubmittingJobId(null);
    }
  };

  const handleDeleteJob = async (jobId: string, title: string) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"?`)) return;
    setJobs((prev) => prev.filter((j) => j.id !== jobId));
    try {
      await deleteJobPost(jobId);
      setAlertMsg(`Job requisition "${title}" has been deleted.`);
      setTimeout(() => setAlertMsg(null), 5000);
    } catch (err) {
      console.error("Failed to delete job on backend:", err);
    }
  };

  const filteredJobs = jobs.filter((j) => {
    if (filterStatus === "ALL") return true;
    return j.status === filterStatus;
  });

  return (
    <div className="command-page space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700 pb-6">
        <div>
          <p className="command-eyebrow">Requisition management</p>
          <h1 className="command-title">Job workspace</h1>
          <p className="command-subtitle">
            Manage active requisitions, draft descriptions, send to Admin for approval, and candidate pipelines.
          </p>
        </div>
        <Link href="/recruiter/jobs/new" className="command-button self-start md:self-auto flex items-center gap-1.5">
          <Plus size={15} /> New Requisition
        </Link>
      </div>

      {alertMsg && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center gap-2">
          <FileCheck size={16} />
          <span>{alertMsg}</span>
        </div>
      )}

      {/* Filter Controls */}
      <div className="flex items-center gap-3">
        {["ALL", "PUBLISHED", "DRAFT", "PAUSED", "CLOSED"].map((st) => (
          <button
            key={st}
            onClick={() => setFilterStatus(st)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors ${
              filterStatus === st
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
            }`}
          >
            {st}
          </button>
        ))}
      </div>

      {/* Jobs List Table */}
      {filteredJobs.length === 0 ? (
        <div className="bg-[#111a2c] border border-[#233047] rounded-xl p-12 text-center">
          <div className="text-slate-300 font-medium text-base">No job requisitions found</div>
          <p className="text-slate-500 text-xs mt-1 max-w-sm mx-auto">
            Create a job requisition to define job requirements, activate candidate AI pipelines, and submit to Admin for approval.
          </p>
          <Link
            href="/recruiter/jobs/new"
            className="inline-block mt-4 text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded-lg transition-colors shadow-md"
          >
            + Create First Job
          </Link>
        </div>
      ) : (
        <div className="command-card overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-700/60 text-slate-400 bg-slate-950/40 uppercase tracking-wider text-[10px]">
                <th className="p-4">Title</th>
                <th className="p-4">Department</th>
                <th className="p-4">Location</th>
                <th className="p-4">Type</th>
                <th className="p-4">Status</th>
                <th className="p-4">Admin Approval</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {filteredJobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 font-medium text-white">
                    <Link href={`/recruiter/jobs/${job.id}/ranking`} className="hover:underline text-sky-300 font-semibold">
                      {job.title}
                    </Link>
                  </td>
                  <td className="p-4 text-slate-300">{job.department || "Engineering"}</td>
                  <td className="p-4 text-slate-300">{job.location || "Remote"}</td>
                  <td className="p-4 text-slate-400 capitalize">
                    {job.employment_type?.replace("_", " ").toLowerCase() || "Full time"}
                  </td>
                  <td className="p-4">
                    {job.verification_status === "APPROVED" ? (
                      <select
                        value={job.status}
                        onChange={(e) => handleStatusChange(job.id, e.target.value)}
                        className="bg-[#0b1425] text-sky-300 border border-[#233047] rounded px-2.5 py-1 text-xs font-semibold outline-none focus:border-sky-500 transition cursor-pointer"
                      >
                        <option value="PUBLISHED">PUBLISHED</option>
                        <option value="PAUSED">PAUSED</option>
                        <option value="CLOSED">CLOSED</option>
                      </select>
                    ) : (
                      <span className="px-2.5 py-1 rounded text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                        {job.status || "DRAFT"}
                      </span>
                    )}
                  </td>
                  <td className="p-4">
                    {job.verification_status === "PENDING_VERIFICATION" ? (
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 w-fit">
                        <Clock3 size={11} /> Awaiting Admin Approval
                      </span>
                    ) : job.verification_status === "APPROVED" ? (
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1 w-fit">
                        <CheckCircle2 size={11} /> Approved by Admin
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleSendToAdmin(job.id, job.title)}
                        disabled={submittingJobId === job.id}
                        className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-[11px] font-semibold flex items-center gap-1 transition shadow"
                      >
                        <Send size={11} /> {submittingJobId === job.id ? "Sending..." : "Send to Admin for Approval"}
                      </button>
                    )}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <Link
                        href={`/recruiter/jobs/${job.id}/edit`}
                        className="text-xs text-slate-300 hover:text-white font-medium flex items-center gap-1 bg-slate-800 px-2 py-1 rounded border border-slate-700"
                      >
                        <Pencil size={12} /> Edit
                      </Link>
                      <button
                        type="button"
                        onClick={() => handleDeleteJob(job.id, job.title)}
                        className="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1 bg-rose-950/40 hover:bg-rose-900/50 px-2 py-1 rounded border border-rose-800/60 transition cursor-pointer"
                      >
                        <Trash2 size={12} /> Delete
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
  );
}
