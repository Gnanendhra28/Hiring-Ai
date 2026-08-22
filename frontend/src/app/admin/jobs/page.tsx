"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle2,
  FileCheck,
  UserCheck,
  UserPlus,
} from "lucide-react";
import {
  fetchPendingJobsAdmin,
  verifyJobAdmin,
  JobItemData,
} from "@/lib/api";

export default function AdminJobsApprovalPage() {
  const router = useRouter();
  const [pendingJobs, setPendingJobs] = useState<JobItemData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [verifyingJobId, setVerifyingJobId] = useState<string | null>(null);

  useEffect(() => {
    async function loadJobsData() {
      try {
        const pendingJbs = await fetchPendingJobsAdmin().catch(() => []);
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

        {/* Pending Job Posts Verification Queue */}
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
      </div>
    </div>
  );
}
