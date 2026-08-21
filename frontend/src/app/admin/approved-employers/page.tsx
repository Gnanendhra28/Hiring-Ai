"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  CheckCircle2,
  ExternalLink,
  Eye,
  Mail,
  Phone,
  ShieldCheck,
  Trash2,
  UserCheck,
  UserPlus,
  X,
} from "lucide-react";
import {
  fetchApprovedEmployers,
  deleteEmployerProfile,
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
    registration_id: "CIN-U72200KA2026PTC123456",
    linkedin_url: "https://linkedin.com/company/rao-enterprise",
    verification_status: "VERIFIED",
    submitted_at: "2026-08-22T10:00:00Z",
  },
  {
    id: "e2",
    user_id: "u2",
    full_name: "Gnanendhra Joy",
    email: "mattag@iitbhilai.ac.in",
    job_title: "Platform Admin & Lead Architect",
    department: "Executive",
    phone_number: "+91 98765 43210",
    company_name: "Rao Enterprise",
    website_url: "https://raoenterprise.com",
    registration_id: "CIN-U72200KA2026PTC123456",
    linkedin_url: "https://linkedin.com/company/rao-enterprise",
    verification_status: "VERIFIED",
    submitted_at: "2026-08-21T10:00:00Z",
  },
];

export default function ApprovedEmployersPage() {
  const router = useRouter();
  const [approvedEmployers, setApprovedEmployers] = useState<PendingEmployerVerification[]>(defaultApprovedEmployers);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEmployer, setSelectedEmployer] = useState<PendingEmployerVerification | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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

  const handleDeleteEmployer = async (userId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete the employer profile for "${name}"? This action will revoke platform access.`)) return;

    setDeletingId(userId);
    try {
      await deleteEmployerProfile(userId);
      setApprovedEmployers((prev) => prev.filter((emp) => emp.user_id !== userId));
      if (selectedEmployer?.user_id === userId) {
        setSelectedEmployer(null);
      }
    } catch (err) {
      console.error("Failed to delete employer profile:", err);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans relative">
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
              Inspect complete profile details or delete employer accounts verified by Platform Admin.
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
                  <th className="px-5 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b263b] text-slate-200">
                {approvedEmployers.map((emp) => (
                  <tr key={emp.id} className="hover:bg-[#18253a]/50 transition">
                    <td className="px-5 py-4 space-y-1">
                      <div className="font-bold text-white text-sm">{emp.full_name}</div>
                      <div className="text-[11px] text-slate-400">{emp.email}</div>
                      <div className="text-[10px] text-sky-400">{emp.job_title || "Recruiter"} &bull; {emp.phone_number || "+91 98765 43210"}</div>
                    </td>
                    <td className="px-5 py-4 space-y-1">
                      <div className="font-bold text-emerald-300">{emp.company_name || "Rao Enterprise"}</div>
                      <div className="text-[11px] text-slate-300 font-mono bg-[#080e1a] px-2 py-0.5 rounded w-fit border border-slate-800">
                        {emp.registration_id || "CIN-U72200KA2026PTC123456"}
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
                    <td className="px-5 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setSelectedEmployer(emp)}
                          className="px-3 py-1.5 bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/30 rounded text-xs font-semibold flex items-center gap-1.5 transition"
                        >
                          <Eye size={13} /> View Profile Details
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteEmployer(emp.user_id, emp.full_name)}
                          disabled={deletingId === emp.user_id}
                          className="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded transition"
                          title="Delete Profile"
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

      {/* Slide-over Profile Details Modal */}
      {selectedEmployer && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#111a2c] border border-[#233047] rounded-3xl max-w-lg w-full p-6 md:p-8 space-y-6 shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-lg">
                  <ShieldCheck size={22} />
                </div>
                <div>
                  <h3 className="text-xl font-extrabold text-white">{selectedEmployer.full_name}</h3>
                  <span className="text-xs text-sky-400">{selectedEmployer.job_title || "Head of Talent Acquisition"}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedEmployer(null)}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
              >
                <X size={18} />
              </button>
            </div>

            {/* Profile Grid Information */}
            <div className="space-y-4 text-xs">
              <div className="bg-[#080e1a] p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Contact & Account Credentials</div>
                <div className="grid grid-cols-2 gap-3 text-slate-200 pt-1">
                  <div>
                    <span className="text-slate-500 block">Work Email:</span>
                    <strong className="text-white text-xs">{selectedEmployer.email}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Contact Phone:</span>
                    <strong className="text-white text-xs">{selectedEmployer.phone_number || "+91 98765 43210"}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Department:</span>
                    <strong className="text-white text-xs">{selectedEmployer.department || "Human Resources"}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Verification Status:</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 inline-block mt-0.5">
                      VERIFIED REAL EMPLOYER
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-[#080e1a] p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Company Business Registration</div>
                <div className="grid grid-cols-2 gap-3 text-slate-200 pt-1">
                  <div>
                    <span className="text-slate-500 block">Company Name:</span>
                    <strong className="text-emerald-300 text-xs">{selectedEmployer.company_name || "Rao Enterprise"}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Registration ID / GSTIN / CIN:</span>
                    <strong className="text-amber-300 font-mono text-xs">{selectedEmployer.registration_id || "CIN-U72200KA2026PTC123456"}</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Company Website:</span>
                    <a
                      href={selectedEmployer.website_url || "https://raoenterprise.com"}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sky-400 hover:underline flex items-center gap-1 mt-0.5"
                    >
                      {selectedEmployer.website_url || "https://raoenterprise.com"} <ExternalLink size={10} />
                    </a>
                  </div>
                  <div>
                    <span className="text-slate-500 block">LinkedIn Profile:</span>
                    {selectedEmployer.linkedin_url ? (
                      <a
                        href={selectedEmployer.linkedin_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sky-400 hover:underline flex items-center gap-1 mt-0.5"
                      >
                        LinkedIn <ExternalLink size={10} />
                      </a>
                    ) : (
                      <span className="text-slate-500">Not provided</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => handleDeleteEmployer(selectedEmployer.user_id, selectedEmployer.full_name)}
                className="px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition"
              >
                <Trash2 size={14} /> Delete Profile
              </button>
              <button
                type="button"
                onClick={() => setSelectedEmployer(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold transition"
              >
                Close Window
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
