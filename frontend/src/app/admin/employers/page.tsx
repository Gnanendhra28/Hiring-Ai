"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  UserCheck,
  UserPlus,
  Users,
  XCircle,
} from "lucide-react";
import {
  fetchPendingEmployers,
  verifyEmployerProfile,
  PendingEmployerVerification,
} from "@/lib/api";

export default function AdminEmployersApprovalPage() {
  const router = useRouter();
  const [pendingEmployers, setPendingEmployers] = useState<PendingEmployerVerification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadPendingEmployers() {
      try {
        const pending = await fetchPendingEmployers();
        setPendingEmployers(pending);
      } catch (err) {
        console.error("Error loading pending employers:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadPendingEmployers();
  }, []);

  const handleVerifyEmployer = async (userId: string, action: "APPROVE" | "REJECT") => {
    setVerifyingId(userId);
    try {
      const ok = await verifyEmployerProfile(userId, action);
      if (ok) {
        setPendingEmployers((prev) => prev.filter((emp) => emp.user_id !== userId));
      }
    } catch (err) {
      console.error("Error verifying employer:", err);
    } finally {
      setVerifyingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider flex items-center gap-1">
                <UserCheck size={12} /> Employees & Employers Approval Portal
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Approve Employers & Employees Credentials
            </h1>
            <p className="text-slate-400 text-xs md:text-sm max-w-2xl">
              Inspect work email domains, company registration IDs, tax records, and LinkedIn credentials submitted by recruiters for Platform Admin verification.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/add-admin")}
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <UserPlus size={14} /> Add New Admin
            </button>
            <button
              onClick={() => router.push("/admin/jobs")}
              className="px-4 py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              Approve Jobs &rarr;
            </button>
          </div>
        </div>

        {/* Pending Verifications Queue */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="text-emerald-400" size={20} />
              <h2 className="text-lg font-bold text-white">Pending Recruiter & Employer Profiles</h2>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {pendingEmployers.length} Awaiting Verification
            </span>
          </div>

          {pendingEmployers.length === 0 ? (
            <div className="py-14 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
              <UserCheck className="mx-auto text-slate-600" size={36} />
              <div className="text-sm font-semibold text-slate-300">No Pending Employer Profile Verifications</div>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                All submitted recruiter and employer credential verifications have been processed by Platform Admin.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                  <tr>
                    <th className="px-5 py-3">Employer / Recruiter</th>
                    <th className="px-5 py-3">Company & Registration</th>
                    <th className="px-5 py-3">Website & LinkedIn</th>
                    <th className="px-5 py-3">Submitted Date</th>
                    <th className="px-5 py-3 text-right">Verification Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1b263b] text-slate-200">
                  {pendingEmployers.map((emp) => (
                    <tr key={emp.id} className="hover:bg-[#18253a]/50 transition">
                      <td className="px-5 py-4 space-y-1">
                        <div className="font-bold text-white text-sm">{emp.full_name}</div>
                        <div className="text-[11px] text-slate-400">{emp.email}</div>
                        <div className="text-[10px] text-sky-400">{emp.job_title || "Recruiter"} &bull; {emp.phone_number || "No phone"}</div>
                      </td>
                      <td className="px-5 py-4 space-y-1">
                        <div className="font-bold text-emerald-300">{emp.company_name || "Enterprise"}</div>
                        <div className="text-[11px] text-slate-300 font-mono bg-[#080e1a] px-2 py-0.5 rounded w-fit border border-slate-800">
                          {emp.registration_id || "REG-UNSPECIFIED"}
                        </div>
                      </td>
                      <td className="px-5 py-4 space-y-1">
                        {emp.website_url ? (
                          <a href={emp.website_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline flex items-center gap-1">
                            {emp.website_url} <ExternalLink size={10} />
                          </a>
                        ) : (
                          <span className="text-slate-500">No website provided</span>
                        )}
                      </td>
                      <td className="px-5 py-4 text-slate-400">
                        {emp.submitted_at ? new Date(emp.submitted_at).toLocaleDateString() : "Recent"}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => handleVerifyEmployer(emp.user_id, "APPROVE")}
                            disabled={verifyingId === emp.user_id}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center gap-1 shadow transition"
                          >
                            <CheckCircle2 size={13} /> {verifyingId === emp.user_id ? "Verifying..." : "Verify Employer"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleVerifyEmployer(emp.user_id, "REJECT")}
                            disabled={verifyingId === emp.user_id}
                            className="px-2.5 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded text-xs font-medium border border-rose-500/20 transition"
                          >
                            Reject
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
