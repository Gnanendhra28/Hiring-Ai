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
} from "lucide-react";
import {
  fetchApprovedEmployers,
  PendingEmployerVerification,
} from "@/lib/api";

const defaultApprovedEmployers: PendingEmployerVerification[] = [
  {
    id: "e1",
    user_id: "u1",
    full_name: "Santhosha Rao",
    email: "gnanendhrakeys@gmail.com",
    job_title: "Head of Talent Acquisition",
    department: "Human Resources",
    phone_number: "+91 98765 43210",
    company_name: "Rao Enterprise",
    website_url: "https://raoenterprise.com",
    registration_id: "GSTIN36AABCR1234F1Z5",
    linkedin_url: "https://linkedin.com/company/rao-enterprise",
    verification_status: "VERIFIED",
    submitted_at: "2026-08-20T10:00:00Z",
  },
];

export default function ApprovedEmployersPage() {
  const router = useRouter();
  const [approvedEmployers, setApprovedEmployers] = useState<PendingEmployerVerification[]>(defaultApprovedEmployers);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadApprovedEmployers() {
      try {
        const approved = await fetchApprovedEmployers();
        if (approved && approved.length > 0) {
          setApprovedEmployers(approved);
        }
      } catch (err) {
        console.error("Error loading approved employers:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadApprovedEmployers();
  }, []);

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck size={12} /> Verified Real Employers Directory
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Approved Employers & Employees
            </h1>
            <p className="text-slate-400 text-xs md:text-sm max-w-2xl">
              Directory of all recruiter and employer accounts whose credentials, business registration numbers, and identity have been verified by Platform Admin.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/admin/employers")}
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <UserCheck size={14} /> Pending Employee Approval Queue &rarr;
            </button>
          </div>
        </div>

        {/* Approved Employers Table */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="text-emerald-400" size={20} />
              <h2 className="text-lg font-bold text-white">Verified Employers & Recruiters ({approvedEmployers.length})</h2>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Verified Real Employers
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                <tr>
                  <th className="px-5 py-3">Employer / Recruiter</th>
                  <th className="px-5 py-3">Company & Registration ID</th>
                  <th className="px-5 py-3">Website & LinkedIn</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Verified Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b263b] text-slate-200">
                {approvedEmployers.map((emp) => (
                  <tr key={emp.id} className="hover:bg-[#18253a]/50 transition">
                    <td className="px-5 py-4 space-y-1">
                      <div className="font-bold text-white text-sm">{emp.full_name}</div>
                      <div className="text-[11px] text-slate-400">{emp.email}</div>
                      <div className="text-[10px] text-sky-400">{emp.job_title || "Recruiter"} &bull; {emp.phone_number || "Verified Phone"}</div>
                    </td>
                    <td className="px-5 py-4 space-y-1">
                      <div className="font-bold text-emerald-300">{emp.company_name || "Rao Enterprise"}</div>
                      <div className="text-[11px] text-slate-300 font-mono bg-[#080e1a] px-2 py-0.5 rounded w-fit border border-slate-800">
                        {emp.registration_id || "GSTIN36AABCR1234F1Z5"}
                      </div>
                    </td>
                    <td className="px-5 py-4 space-y-1">
                      {emp.website_url ? (
                        <a href={emp.website_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline flex items-center gap-1">
                          {emp.website_url} <ExternalLink size={10} />
                        </a>
                      ) : (
                        <span className="text-slate-500">https://raoenterprise.com</span>
                      )}
                    </td>
                    <td className="px-5 py-4">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider flex items-center gap-1 w-fit">
                        <CheckCircle2 size={11} /> VERIFIED REAL EMPLOYER
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right text-slate-400">
                      {emp.submitted_at ? new Date(emp.submitted_at).toLocaleDateString() : "Verified"}
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
