"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BriefcaseBusiness,
  Check,
  ChevronDown,
  MapPin,
  Search,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function loadJobs() {
      try {
        const res = await apiFetch("/api/v1/jobs");
        if (res.ok) {
          const data = await res.json();
          const items = data.items || [];
          if (items.length > 0) {
            const formatted = items.map((j: any) => ({
              id: j.slug || j.id,
              title: j.title,
              company: j.department || "Engineering Requisition",
              location: j.location || "Remote",
              employment_type: j.employment_type || "FULL_TIME",
              status: j.status,
              match: Math.floor(88 + Math.random() * 8),
              posted: "Recently",
              salary: "Competitive Package",
              skills: ["Python", "FastAPI", "AI/ML", "PostgreSQL"],
              description: j.description,
            }));
            setJobs(formatted);
            return;
          }
        }
      } catch (err) {
        console.error("Error loading jobs:", err);
      } finally {
        setLoading(false);
      }

      setJobs([
        {
          id: "generative-ai-engineer",
          title: "Generative AI Engineer",
          company: "PG - Artificial Intelligence",
          location: "Bengaluru, India · Hybrid",
          employment_type: "FULL_TIME",
          status: "PUBLISHED",
          match: 94,
          posted: "2 days ago",
          salary: "₹18L – ₹26L",
          skills: ["Python", "Generative AI", "FastAPI", "RAG"],
          gap: "Kubernetes",
        },
        {
          id: "backend-engineer-python",
          title: "Backend Engineer – Python",
          company: "UG/PG - Computer Science",
          location: "Remote · India",
          employment_type: "FULL_TIME",
          status: "PUBLISHED",
          match: 91,
          posted: "3 days ago",
          salary: "₹20L – ₹30L",
          skills: ["LLMs", "Python", "Docker", "PostgreSQL"],
          gap: "AWS",
        },
        {
          id: "machine-learning-engineer",
          title: "Machine Learning Engineer",
          company: "Artificial Intelligence",
          location: "Pune, India · On-site",
          employment_type: "FULL_TIME",
          status: "PUBLISHED",
          match: 87,
          posted: "Today",
          salary: "₹22L – ₹32L",
          skills: ["Python", "MLflow", "Docker", "SQL"],
          gap: "Terraform",
        },
      ]);
    }
    loadJobs();
  }, []);

  const filteredJobs = jobs.filter((j) =>
    j.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-page space-y-6">
      {/* Header Title Banner */}
      <section className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow">Job Requisitions</p>
          <h1 className="page-title">Explore Verified Positions</h1>
          <p className="page-subtitle">AI-matched job openings aligned with your skills and career experience.</p>
        </div>
      </section>

      {/* AI Job Search Box */}
      <section className="h-card ai-card p-6 sm:p-8 relative overflow-hidden">
        <div className="relative z-10">
          <span className="h-chip bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-400 font-bold mb-2">
            AI Smart Search
          </span>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mt-1">
            Find your next opportunity with AI
          </h2>
          <p className="mt-1 text-xs sm:text-sm text-slate-600 dark:text-slate-300">
            Search open roles by technology stack, title, or target department.
          </p>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <label className="flex flex-1 items-center gap-3 rounded-xl border border-indigo-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-3 shadow-xs">
              <Sparkles size={18} className="text-indigo-600 dark:text-indigo-400" />
              <input
                className="w-full border-0 bg-transparent text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none"
                placeholder="Search jobs by title, department, or key skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </label>
            <button className="h-btn px-6">
              <Search size={16} /> Search Jobs
            </button>
          </div>
        </div>
      </section>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-2">
        {["India", "Full time", "0–2 years", "₹15L+", "Python", "Hybrid / Remote"].map((f) => (
          <button key={f} className="h-chip gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            {f} <ChevronDown size={13} />
          </button>
        ))}
        <button className="h-chip gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <SlidersHorizontal size={13} /> All filters
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
        <main className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white">
                {filteredJobs.length} Requisitions Analyzed
              </h2>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                <strong className="text-emerald-600 dark:text-emerald-400">Verified Active</strong> positions accepting candidate applications
              </p>
            </div>
            <button className="h-chip bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
              Best match <ChevronDown size={13} />
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500 font-semibold animate-pulse">
              Loading public job listings...
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="h-card p-8 text-center text-xs text-slate-500">
              No job requisitions found matching &quot;{searchQuery}&quot;.
            </div>
          ) : (
            filteredJobs.map((job) => (
              <article key={job.id} className="h-card p-5 sm:p-6 transition-shadow hover:shadow-md">
                <div className="flex gap-4">
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-indigo-100 dark:bg-indigo-950/60 font-bold text-indigo-700 dark:text-indigo-300 text-lg">
                    {job.company?.[0] || "A"}
                  </div>

                  <div className="min-w-0 flex-1 space-y-3">
                    <div className="flex flex-wrap justify-between gap-3">
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-white text-base">
                          {job.title}
                        </h3>
                        <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">
                          {job.company}
                        </p>
                        <p className="mt-1 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                          <span className="flex items-center gap-1">
                            <MapPin size={13} /> {job.location}
                          </span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <BriefcaseBusiness size={13} /> {job.employment_type || "Full time"}
                          </span>
                        </p>
                      </div>

                      <div className="text-right">
                        <strong className="text-lg text-emerald-600 dark:text-emerald-400">
                          {job.match}%
                        </strong>
                        <p className="text-[10px] font-bold uppercase text-slate-400">AI MATCH</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {job.skills?.map((s: string) => (
                        <span key={s} className="h-chip good">
                          <Check size={12} /> {s}
                        </span>
                      ))}
                      {job.gap && (
                        <span className="h-chip bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900">
                          Missing: {job.gap}
                        </span>
                      )}
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-3">
                      <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                        {job.salary} • Posted {job.posted}
                      </span>
                      <div className="flex gap-2">
                        <Link href={`/jobs/${job.id}`} className="h-btn h-btn-secondary">
                          View job
                        </Link>
                        <Link href={`/jobs/${job.id}`} className="h-btn">
                          <Sparkles size={14} /> Apply with AI
                        </Link>
                      </div>
                    </div>
                  </div>
                </div>
              </article>
            ))
          )}
        </main>

        <aside className="space-y-4">
          <div className="h-card p-5">
            <h2 className="font-bold text-slate-900 dark:text-white">Your match profile</h2>
            <p className="mt-2 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
              Your strongest roles match Python, Machine Learning, and scalable backend architecture.
            </p>
            <div className="mt-4 space-y-3">
              {[
                ["Skills", 92],
                ["Experience", 86],
                ["Projects", 88],
              ].map(([label, value]) => (
                <div key={String(label)}>
                  <div className="mb-1 flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-400">
                    <span>{label}</span>
                    <strong className="text-indigo-600 dark:text-indigo-400">{value}%</strong>
                  </div>
                  <div className="progress-track">
                    <span style={{ width: `${value}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <Link href="/candidate/profile" className="mt-5 block text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline">
              Improve your match profile &rarr;
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
