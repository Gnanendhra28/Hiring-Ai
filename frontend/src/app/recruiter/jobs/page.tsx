"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { fetchRecruiterJobs, updateJobStatus, JobItemData } from "@/lib/api";

const defaultSampleJobs: JobItemData[] = [
  {
    id: "senior-ml",
    title: "Senior ML Engineer",
    slug: "senior-ml-engineer",
    description: "",
    department: "Applied AI",
    location: "Bengaluru",
    employment_type: "Full time",
    status: "PUBLISHED",
    verification_status: "APPROVED",
    created_at: "2026-08-18",
  },
  {
    id: "product-designer",
    title: "Product Designer",
    slug: "product-designer",
    description: "",
    department: "Product",
    location: "Remote",
    employment_type: "Full time",
    status: "PUBLISHED",
    verification_status: "APPROVED",
    created_at: "2026-08-16",
  },
  {
    id: "ai-platform",
    title: "AI Platform Engineer",
    slug: "ai-platform-engineer",
    description: "",
    department: "Engineering",
    location: "Bengaluru",
    employment_type: "Full time",
    status: "DRAFT",
    verification_status: "APPROVED",
    created_at: "2026-08-20",
  },
];

export default function JobWorkspaceListPage() {
  const [jobs, setJobs] = useState<JobItemData[]>(defaultSampleJobs);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  const loadJobs = async () => {
    try {
      const liveJobs = await fetchRecruiterJobs();
      if (liveJobs && liveJobs.length > 0) {
        setJobs(liveJobs);
      }
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
            Manage active requisitions, draft descriptions, and candidate pipelines.
          </p>
        </div>
        <Link href="/recruiter/jobs/new" className="command-button self-start md:self-auto flex items-center gap-1.5">
          <Plus size={15} /> New Requisition
        </Link>
      </div>

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
            Create a job requisition to define job requirements, activate candidate AI pipelines, and start receiving applications.
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
                    <select
                      value={job.status}
                      onChange={(e) => handleStatusChange(job.id, e.target.value)}
                      className="bg-[#0b1425] text-sky-300 border border-[#233047] rounded px-2.5 py-1 text-xs font-semibold outline-none focus:border-sky-500 transition cursor-pointer"
                    >
                      <option value="PUBLISHED">PUBLISHED</option>
                      <option value="DRAFT">DRAFT</option>
                      <option value="PAUSED">PAUSED</option>
                      <option value="CLOSED">CLOSED</option>
                    </select>
                  </td>
                  <td className="p-4 text-right">
                    <Link href={`/recruiter/jobs/${job.id}/ranking`} className="text-xs text-sky-300 hover:text-sky-200 font-semibold">
                      Open Workspace &rarr;
                    </Link>
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

