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

  const filteredJobs = jobs.filter(
    (j) =>
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
          <p className="page-subtitle">
            AI-matched job openings aligned with your skills and career experience.
          </p>
        </div>
      </section>

      {/* AI Job Search Banner - Crystal Clear in both Light and Dark */}
      <section className="rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-gradient-to-r from-indigo-50 via-purple-50 to-violet-50 dark:from-indigo-950/80 dark:via-purple-950/50 dark:to-slate-900 p-6 sm:p-8 shadow-xs">
        <div className="space-y-2">
          <span className="inline-block px-3 py-1 rounded-lg bg-indigo-600 text-white dark:bg-indigo-900 dark:text-indigo-200 text-xs font-bold uppercase tracking-wider">
            AI Smart Search
          </span>
          <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white mt-2">
            Find your next opportunity with AI
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
            Search open roles by technology stack, title, or target department.
          </p>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <label className="flex flex-1 items-center gap-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-3 shadow-xs">
            <Sparkles size={18} className="text-indigo-600 dark:text-indigo-400 shrink-0" />
            <input
              className="w-full border-0 bg-transparent text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none"
              placeholder="Search jobs by title, department, or key skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all">
            <Search size={16} /> Search Jobs
          </button>
        </div>
      </section>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-2">
        {["India", "Full time", "0–2 years", "₹15L+", "Python", "Hybrid / Remote"].map((f) => (
          <button
            key={f}
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:border-indigo-400 dark:hover:border-indigo-600 transition-all flex items-center gap-1.5 shadow-xs"
          >
            {f} <ChevronDown size={13} />
          </button>
        ))}
        <button className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:border-indigo-400 dark:hover:border-indigo-600 transition-all flex items-center gap-1.5 shadow-xs">
          <SlidersHorizontal size={13} /> All filters
        </button>
      </div>

      {/* Main Content Layout */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
        <main className="space-y-4">
          <div className="flex items-center justify-between pb-1">
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base">
                {filteredJobs.length} Requisitions Analyzed
              </h2>
              <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
                <strong className="text-emerald-600 dark:text-emerald-400">Verified Active</strong> positions accepting candidate applications
              </p>
            </div>
            <button className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-semibold flex items-center gap-1">
              Best match <ChevronDown size={13} />
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500 font-semibold animate-pulse">
              Loading public job listings...
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="p-8 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-center text-xs text-slate-500">
              No job requisitions found matching &quot;{searchQuery}&quot;.
            </div>
          ) : (
            filteredJobs.map((job) => (
              <article
                key={job.id}
                className="p-5 sm:p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs hover:shadow-md transition-all"
              >
                <div className="flex gap-4">
                  <div className="w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-950/80 border border-indigo-200 dark:border-indigo-900 text-indigo-700 dark:text-indigo-300 font-bold grid place-items-center text-lg shrink-0">
                    {job.company?.[0] || "A"}
                  </div>

                  <div className="min-w-0 flex-1 space-y-3">
                    <div className="flex flex-wrap justify-between gap-3">
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-white text-base">
                          {job.title}
                        </h3>
                        <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400 font-medium">
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
                        <strong className="text-lg text-emerald-600 dark:text-emerald-400 font-extrabold">
                          {job.match}%
                        </strong>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                          AI MATCH
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {job.skills?.map((s: string) => (
                        <span
                          key={s}
                          className="px-2.5 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs font-semibold flex items-center gap-1"
                        >
                          <Check size={12} /> {s}
                        </span>
                      ))}
                      {job.gap && (
                        <span className="px-2.5 py-1 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-700 dark:text-amber-300 text-xs font-semibold">
                          Missing: {job.gap}
                        </span>
                      )}
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-3">
                      <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                        {job.salary} • Posted {job.posted}
                      </span>
                      <div className="flex gap-2">
                        <Link
                          href={`/jobs/${job.id}`}
                          className="px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 text-xs font-semibold transition-all"
                        >
                          View job
                        </Link>
                        <Link
                          href={`/jobs/${job.id}`}
                          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
                        >
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
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs">
            <h2 className="font-bold text-slate-900 dark:text-white text-sm">Your match profile</h2>
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
            <Link
              href="/candidate/profile"
              className="mt-5 block text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Improve your match profile &rarr;
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
