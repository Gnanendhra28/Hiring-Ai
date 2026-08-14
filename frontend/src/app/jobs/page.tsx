"use client";

import React, { useState } from "react";
import Link from "next/link";

interface PublicJob {
  id: string;
  title: string;
  slug: string;
  organization_name: string;
  department: string | null;
  location: string | null;
  employment_type: string;
  description: string;
  created_at: string;
}

export default function PublicJobDirectoryPage() {
  const [jobs] = useState<PublicJob[]>([
    {
      id: "1",
      title: "Staff Backend Engineer - Python",
      slug: "staff-backend-engineer-python-a1b2c3",
      organization_name: "Acme AI Systems",
      department: "Engineering",
      location: "Remote / Austin, TX",
      employment_type: "FULL_TIME",
      description: "Architecting high-scale distributed backend services using Python 3.13, FastAPI, and PostgreSQL pgvector.",
      created_at: "2026-08-14T10:00:00Z",
    },
  ]);
  const [searchTerm, setSearchTerm] = useState("");

  const filteredJobs = jobs.filter(
    (j) =>
      j.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      j.organization_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (j.department && j.department.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Public Job Directory</h1>
            <p className="text-slate-400 text-sm mt-1">Explore verified requisitions across top hiring organizations.</p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/candidate/dashboard"
              className="text-xs bg-slate-900 border border-slate-800 hover:bg-slate-800 px-4 py-2 rounded-lg text-slate-300 transition-colors"
            >
              Candidate Portal &rarr;
            </Link>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
          <input
            type="text"
            placeholder="Search by job title, department, or company..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Job Listings Grid */}
        <div className="space-y-4">
          {filteredJobs.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-800 rounded-xl">
              <div className="text-slate-400 font-medium">No published jobs matching your search</div>
              <p className="text-slate-500 text-xs mt-1">Check back soon for new open positions.</p>
            </div>
          ) : (
            filteredJobs.map((job) => (
              <div
                key={job.id}
                className="bg-slate-900/40 border border-slate-800 hover:border-slate-700 rounded-xl p-6 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                      {job.organization_name}
                    </span>
                    <span className="text-slate-600">&bull;</span>
                    <span className="text-xs text-slate-400">{job.department || "General"}</span>
                  </div>
                  <h2 className="text-lg font-bold text-white">
                    <Link href={`/jobs/${job.slug}`} className="hover:underline">
                      {job.title}
                    </Link>
                  </h2>
                  <p className="text-xs text-slate-400 line-clamp-2 max-w-2xl">{job.description}</p>
                  <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-1">
                    <span>📍 {job.location || "Remote"}</span>
                    <span>💼 {job.employment_type}</span>
                  </div>
                </div>
                <div>
                  <Link
                    href={`/jobs/${job.slug}`}
                    className="inline-block px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all whitespace-nowrap"
                  >
                    View & Apply &rarr;
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
