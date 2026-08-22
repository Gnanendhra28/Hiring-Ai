"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  ChevronRight,
  Clock3,
  ExternalLink,
  FileCheck,
  Pencil,
  Plus,
  ShieldCheck,
  Sparkles,
  Trash2,
  UserCheck,
  UserPlus,
  UsersRound,
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import {
  fetchRecruiterJobs,
  updateJobStatus,
  deleteJobPost,
  fetchPendingEmployers,
  fetchApprovedEmployers,
  verifyEmployerProfile,
  fetchPendingJobsAdmin,
  fetchAllJobsAdmin,
  verifyJobAdmin,
  JobItemData,
  PendingEmployerVerification,
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

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [jobs, setJobs] = useState<LocalJobDisplay[]>([]);
  const [pendingEmployers, setPendingEmployers] = useState<PendingEmployerVerification[]>([]);
  const [approvedEmployers, setApprovedEmployers] = useState<PendingEmployerVerification[]>([]);
  const [pendingJobs, setPendingJobs] = useState<JobItemData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [verifyingEmpId, setVerifyingEmpId] = useState<string | null>(null);
  const [verifyingJobId, setVerifyingJobId] = useState<string | null>(null);

  useEffect(() => {
    async function loadAdminDashboardData() {
      try {
        // 1. Fetch live platform jobs across all organizations
        const liveJobs = await fetchAllJobsAdmin();
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

        // 2. Fetch pending employer profile verifications
        const pendingEmps = await fetchPendingEmployers();
        setPendingEmployers(pendingEmps);

        // 3. Fetch approved employers
        const approvedEmps = await fetchApprovedEmployers();
        setApprovedEmployers(approvedEmps);

        // 4. Fetch pending job post requisitions
        const pendingJbs = await fetchPendingJobsAdmin();
        setPendingJobs(pendingJbs);
      } catch (err) {
        console.error("Error loading Admin Dashboard data:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadAdminDashboardData();
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
    if (!confirm("Are you sure you want to delete this job posting from the platform?")) return;
    setJobs((prev) => prev.filter((j) => j.id !== jobId));
    try {
      await deleteJobPost(jobId);
    } catch (err) {
      console.error("Failed to delete job:", err);
    }
  };

  const handleVerifyEmployer = async (userId: string, action: "APPROVE" | "REJECT") => {
    setVerifyingEmpId(userId);
    try {
      const ok = await verifyEmployerProfile(userId, action);
      if (ok) {
        setPendingEmployers((prev) => prev.filter((emp) => emp.user_id !== userId));
      }
    } catch (err) {
      console.error("Error verifying employer:", err);
    } finally {
      setVerifyingEmpId(null);
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

  const userName = user?.full_name || "Gnanendhra Joy";
  const approvedJobsCount = jobs.filter((j) => j.status === "ACTIVE").length;
  const approvedEmployeesCount = approvedEmployers.length > 0 ? approvedEmployers.length : 1;

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Admin Control Banner Header */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="space-y-2 relative z-10">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck size={12} /> Platform Admin Verification Console
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
              Welcome, {userName} 👋
            </h1>
            <p className="text-slate-400 text-xs md:text-sm max-w-2xl">
              Inspect, verify, and approve employer/employee profile credentials and job postings created by recruiters across the platform.
            </p>
          </div>

          <div className="flex items-center gap-3 relative z-10">
            <Link
              href="/admin/jobs"
              className="px-4 py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <FileCheck size={15} /> Approve Jobs
            </Link>
            <Link
              href="/admin/employers"
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <UserCheck size={15} /> Approve Employees
            </Link>
            <Link
              href="/admin/add-admin"
              className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5 shadow"
            >
              <UserPlus size={15} /> Add Admin
            </Link>
          </div>
        </div>

        {/* Stat Cards Grid: Approved Employees, Pending Employees, Approved Jobs, Pending Jobs */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          <Link
            href="/admin/approved-employers"
            className="bg-[#111a2c] hover:bg-[#152238] border border-[#233047] rounded-xl p-5 transition shadow-lg group cursor-pointer"
          >
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider">Approved Employees</span>
              <ShieldCheck size={18} className="text-emerald-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-3xl font-extrabold text-emerald-400 mt-3">{approvedEmployeesCount}</div>
            <div className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1">
              Verified Employer Profiles <ChevronRight size={12} />
            </div>
          </Link>

          <Link
            href="/admin/employers"
            className="bg-[#111a2c] hover:bg-[#152238] border border-[#233047] rounded-xl p-5 transition shadow-lg group cursor-pointer"
          >
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider">Pending Employees</span>
              <UserCheck size={18} className="text-amber-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-3xl font-extrabold text-amber-400 mt-3">{pendingEmployers.length}</div>
            <div className="text-[11px] text-amber-400 mt-2 flex items-center gap-1">
              Awaiting Admin Verification <ChevronRight size={12} />
            </div>
          </Link>

          <Link
            href="/admin/approved-jobs"
            className="bg-[#111a2c] hover:bg-[#152238] border border-[#233047] rounded-xl p-5 transition shadow-lg group cursor-pointer"
          >
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider">Approved Jobs</span>
              <CheckCircle2 size={18} className="text-sky-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-3xl font-extrabold text-sky-400 mt-3">{approvedJobsCount}</div>
            <div className="text-[11px] text-sky-400 mt-2 flex items-center gap-1">
              Published Active Postings <ChevronRight size={12} />
            </div>
          </Link>

          <Link
            href="/admin/jobs"
            className="bg-[#111a2c] hover:bg-[#152238] border border-[#233047] rounded-xl p-5 transition shadow-lg group cursor-pointer"
          >
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider">Pending Jobs</span>
              <FileCheck size={18} className="text-rose-400 group-hover:scale-110 transition-transform" />
            </div>
            <div className="text-3xl font-extrabold text-rose-400 mt-3">{pendingJobs.length}</div>
            <div className="text-[11px] text-rose-400 mt-2 flex items-center gap-1">
              Awaiting Job Approval <ChevronRight size={12} />
            </div>
          </Link>
        </div>

        {/* TASK 1: Pending Employer / Employee Profile Verification Queue */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Building2 className="text-emerald-400" size={20} />
              <h2 className="text-lg font-bold text-white">1. Verify Employer / Employee Profiles</h2>
            </div>
            <Link href="/admin/employers" className="text-xs text-sky-400 hover:underline">
              View Employees Approval Page &rarr;
            </Link>
          </div>

          {pendingEmployers.length === 0 ? (
            <div className="py-10 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
              <UserCheck className="mx-auto text-slate-600" size={32} />
              <div className="text-sm font-semibold text-slate-300">No Pending Employer Profile Verifications</div>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                All submitted recruiter profile credentials have been verified by Platform Admin.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                  <tr>
                    <th className="px-5 py-3">Employer / Recruiter</th>
                    <th className="px-5 py-3">Company & Registration ID</th>
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
                            disabled={verifyingEmpId === emp.user_id}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center gap-1 shadow transition"
                          >
                            <CheckCircle2 size={13} /> {verifyingEmpId === emp.user_id ? "Verifying..." : "Verify Employer"}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleVerifyEmployer(emp.user_id, "REJECT")}
                            disabled={verifyingEmpId === emp.user_id}
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

        {/* TASK 2: Pending Job Posts Verification Queue */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <FileCheck className="text-amber-400" size={20} />
              <h2 className="text-lg font-bold text-white">2. Verify Job Postings Created by Employees</h2>
            </div>
            <Link href="/admin/jobs" className="text-xs text-sky-400 hover:underline">
              View Jobs Approval Page &rarr;
            </Link>
          </div>

          {pendingJobs.length === 0 ? (
            <div className="py-10 text-center border border-dashed border-slate-800 rounded-xl space-y-2">
              <CheckCircle2 className="mx-auto text-slate-600" size={32} />
              <div className="text-sm font-semibold text-slate-300">No Job Requisitions Awaiting Verification</div>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                All submitted recruiter job postings have been reviewed and approved for publication.
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
