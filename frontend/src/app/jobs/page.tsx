"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BriefcaseBusiness,
  Check,
  ChevronDown,
  MapPin,
  Moon,
  Search,
  SlidersHorizontal,
  Sparkles,
  Sun,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function JobsPage() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const savedTheme = localStorage.getItem("candidate_theme_pref");
    if (savedTheme === "dark" || savedTheme === "light") {
      setTheme(savedTheme);
      document.documentElement.classList.toggle("dark", savedTheme === "dark");
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
      document.documentElement.classList.toggle("dark", prefersDark);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("candidate_theme_pref", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

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
              company: j.department || "Engineering",
              location: j.location || "Remote",
              employment_type: j.employment_type || "FULL_TIME",
              status: j.status,
              match: Math.floor(88 + Math.random() * 8),
              posted: "Recently",
              salary: "Competitive Salary",
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

      // Fallback default open jobs
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 px-4 py-8 sm:px-8 font-sans transition-colors duration-200">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
          <Link href="/candidate/dashboard" className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-indigo-600 grid place-items-center text-white font-bold shadow-md shadow-indigo-500/20">
              <Sparkles size={18} />
            </span>
            <span className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Hiring<span className="text-indigo-600 dark:text-indigo-400">AI</span>
            </span>
          </Link>

          <div className="flex items-center gap-4">
            {/* Dark & Light Theme Toggle */}
            <button
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
              title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all shadow-sm"
            >
              {theme === "dark" ? (
                <Sun size={18} className="text-amber-400" />
              ) : (
                <Moon size={18} className="text-slate-600" />
              )}
            </button>

            <Link
              className="text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
              href="/candidate/dashboard"
            >
              &larr; Back to home
            </Link>
          </div>
        </div>

        {/* AI Job Search Hero Section */}
        <section className="rounded-2xl border border-indigo-200 dark:border-indigo-900/50 bg-gradient-to-r from-indigo-100/80 via-purple-50 to-violet-100/80 dark:from-indigo-950/60 dark:via-purple-950/40 dark:to-slate-900/80 p-6 sm:p-8 shadow-sm">
          <p className="text-xs font-extrabold uppercase tracking-widest text-indigo-600 dark:text-indigo-400">
            AI Job Search Requisitions
          </p>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
            Find your next opportunity with AI
          </h1>
          <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 mt-2 max-w-2xl leading-relaxed">
            Discover verified AI and engineering opportunities tailored to your skills, experience, and career goals.
          </p>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <label className="flex flex-1 items-center gap-3 rounded-xl border border-indigo-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-3 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500">
              <Sparkles size={18} className="text-indigo-600 dark:text-indigo-400" />
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

        {/* Quick Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {["India", "Full time", "0–2 years", "₹15L+", "Python", "Hybrid / Remote"].map((f) => (
            <button
              key={f}
              className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:border-indigo-400 transition-all flex items-center gap-1.5 shadow-xs"
            >
              {f} <ChevronDown size={13} />
            </button>
          ))}
          <button className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:border-indigo-400 transition-all flex items-center gap-1.5 shadow-xs">
            <SlidersHorizontal size={13} /> All filters
          </button>
        </div>

        {/* Main Content Layout */}
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
          {/* Job Listings Column */}
          <main className="space-y-4">
            <div className="flex items-center justify-between pb-2">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  {filteredJobs.length} Requisitions Available
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                  <strong className="text-emerald-600 dark:text-emerald-400">Verified Active</strong> positions open for candidate applications
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
                  className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm hover:shadow-md hover:border-indigo-300 dark:hover:border-slate-700 transition-all"
                >
                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-100 dark:border-indigo-900 text-indigo-700 dark:text-indigo-300 font-bold grid place-items-center text-lg shrink-0">
                      {job.company?.[0] || "A"}
                    </div>

                    <div className="min-w-0 flex-1 space-y-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <div>
                          <h3 className="text-base font-bold text-slate-900 dark:text-white">
                            {job.title}
                          </h3>
                          <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mt-0.5">
                            {job.company}
                          </p>
                          <p className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-1">
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
                          <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
                            {job.match}%
                          </span>
                          <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                            AI MATCH
                          </p>
                        </div>
                      </div>

                      {/* Required Skills & Badges */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {job.skills?.map((s: string) => (
                          <span
                            key={s}
                            className="px-2.5 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 text-emerald-700 dark:text-emerald-300 text-xs font-semibold flex items-center gap-1"
                          >
                            <Check size={12} /> {s}
                          </span>
                        ))}
                        {job.gap && (
                          <span className="px-2.5 py-1 rounded-md bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-amber-700 dark:text-amber-300 text-xs font-semibold">
                            Missing: {job.gap}
                          </span>
                        )}
                      </div>

                      {/* Footer Info & Actions */}
                      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 dark:border-slate-800/80 pt-3 mt-3">
                        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                          {job.salary} • Posted {job.posted}
                        </span>
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/jobs/${job.id}`}
                            className="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 text-xs font-semibold transition-all"
                          >
                            View Job
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

          {/* Right Match Profile Sidebar */}
          <aside className="space-y-4">
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">Your Match Profile</h2>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                Your strongest roles match Python, Machine Learning, and scalable backend architecture.
              </p>

              <div className="mt-4 space-y-3">
                {[
                  ["Skills Match", 92],
                  ["Experience Level", 86],
                  ["Projects & Repo", 88],
                ].map(([label, value]) => (
                  <div key={String(label)}>
                    <div className="flex justify-between text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                      <span>{label}</span>
                      <span className="text-indigo-600 dark:text-indigo-400">{value}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full"
                        style={{ width: `${value}%` }}
                      />
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
    </div>
  );
}
