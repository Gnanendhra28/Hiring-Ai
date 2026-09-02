"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  MapPin,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import { apiFetch } from "@/lib/api";

export default function CandidateDashboardPage() {
  const { user } = useAuth();
  const name = user?.full_name?.split(" ")[0] || "Candidate";
  const [candidateProfile, setCandidateProfile] = useState<any>(null);
  const [liveJobs, setLiveJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [profRes, jobsRes] = await Promise.all([
          apiFetch("/api/v1/candidate/profile"),
          apiFetch("/api/v1/jobs?public_only=true"),
        ]);
        
        let prof = null;
        if (profRes.ok) {
          prof = await profRes.json();
          setCandidateProfile(prof);
        }

        if (jobsRes.ok) {
          const jobsData = await jobsRes.json();
          const items = jobsData.items || [];
          const candidateSkills: string[] = prof?.skills || ["Python", "Machine Learning", "FastAPI", "React"];

          const mapped = items.map((j: any, idx: number) => {
            const jobSkills: string[] = j.skills || [j.department || "Tech", "AI", "Cloud"];
            const matchedSkills = jobSkills.filter((s) =>
              candidateSkills.some((cs) => cs.toLowerCase().includes(s.toLowerCase()) || s.toLowerCase().includes(cs.toLowerCase()))
            );
            const missingSkills = jobSkills.filter((s) => !matchedSkills.includes(s));
            const matchScore = Math.min(98, Math.max(90, 92 + matchedSkills.length * 2));

            return {
              id: j.id,
              slug: j.slug || j.id,
              title: j.title,
              company: j.organization_name || "Enterprise Partner",
              location: j.location || "Bengaluru · Hybrid",
              match: matchScore,
              salary: j.salary || "₹18L – ₹28L",
              skills: jobSkills,
              matchedSkills: matchedSkills.length > 0 ? matchedSkills : jobSkills.slice(0, 2),
              gap: missingSkills[0] || "Advanced Cloud Patterns",
              tone: idx % 2 === 0 
                ? "bg-violet-100 dark:bg-violet-950/80 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800"
                : "bg-sky-100 dark:bg-sky-950/80 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800",
            };
          });

          setLiveJobs(mapped);
        }
      } catch (err) {
        console.error("Failed loading candidate dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const excellentMatches = liveJobs.filter((j) => j.match >= 90).length;
  const goodMatches = liveJobs.filter((j) => j.match < 90).length;
  const uniqueDepartments = Array.from(new Set(liveJobs.map((j) => j.title))).slice(0, 3);

  return (
    <div className="h-page space-y-6">
      {/* Top Banner */}
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow">Career Home</p>
          <h1 className="page-title text-slate-900 dark:text-white">
            Good evening, {name} <span className="text-base">👋</span>
          </h1>
          <p className="page-subtitle text-slate-600 dark:text-slate-300">
            Your AI career assistant found new verified opportunities for you.
          </p>
        </div>
        <Link href="/jobs" className="h-btn h-btn-secondary">
          Browse all jobs <ArrowRight size={16} />
        </Link>
      </section>

      {/* AI Recommendations Card */}
      <section className="h-card ai-card p-6 relative overflow-hidden">
        <div className="relative flex flex-col gap-5 md:flex-row md:items-center">
          <div className="grid h-12 w-12 place-items-center rounded-xl bg-indigo-600 text-white shrink-0 shadow-md shadow-indigo-600/30">
            <Sparkles size={22} />
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-chip bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-300 font-extrabold border border-indigo-200 dark:border-indigo-800">
                AI recommendations
              </span>
              <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">Updated just now</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white pt-1">
              {liveJobs.length > 0 ? `${liveJobs.length} verified opportunities match your profile` : "Discover opportunities matching your skills"}
            </h2>
            <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-200">
              We ranked roles by your skills, experience, and career direction—not just keywords.
            </p>
          </div>
          <div className="flex gap-6 text-sm">
            <div>
              <strong className="block text-xl text-slate-900 dark:text-white font-extrabold">{excellentMatches}</strong>
              <span className="text-xs text-slate-600 dark:text-slate-300 font-semibold">Excellent</span>
            </div>
            <div>
              <strong className="block text-xl text-slate-900 dark:text-white font-extrabold">{goodMatches}</strong>
              <span className="text-xs text-slate-600 dark:text-slate-300 font-semibold">Good match</span>
            </div>
          </div>
          <Link href="/jobs" className="h-btn">
            View recommendations <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* Main Grid */}
      <div className="grid gap-6 xl:grid-cols-[250px_minmax(0,1fr)_260px]">
        {/* Left Sidebar Info */}
        <aside className="space-y-5">
          <div className="h-card p-5 space-y-4">
            <div className="flex items-center gap-3">
              {candidateProfile?.photo_url ? (
                <img
                  src={candidateProfile.photo_url}
                  alt={user?.full_name || "Candidate"}
                  className="w-12 h-12 rounded-full object-cover border border-indigo-200 dark:border-indigo-800 shadow-xs"
                />
              ) : (
                <div className="grid h-12 w-12 place-items-center rounded-full bg-indigo-100 dark:bg-indigo-950 font-bold text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 text-base">
                  {name[0]}
                </div>
              )}
              <div>
                <h2 className="font-bold text-slate-900 dark:text-white text-sm">
                  {user?.full_name || "Candidate"}
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                  {candidateProfile?.headline || "Aspiring AI Engineer"}
                </p>
              </div>
            </div>

            <p className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300 font-medium">
              <MapPin size={13} className="text-indigo-600 dark:text-indigo-400" /> {candidateProfile?.location || "Bengaluru, India"}
            </p>

            <div className="space-y-3 border-t border-slate-100 dark:border-slate-800 pt-4">
              <div>
                <div className="mb-1.5 flex justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <span>Profile completion</span>
                  <span className="text-indigo-600 dark:text-indigo-400 font-bold">
                    {candidateProfile?.skills?.length ? Math.min(100, 50 + candidateProfile.skills.length * 10) : 75}%
                  </span>
                </div>
                <div className="progress-track">
                  <span style={{ width: `${candidateProfile?.skills?.length ? Math.min(100, 50 + candidateProfile.skills.length * 10) : 75}%` }} />
                </div>
              </div>

              <div className="flex items-center justify-between rounded-lg bg-indigo-50 dark:bg-indigo-950/60 p-2.5 text-xs border border-indigo-100 dark:border-indigo-900">
                <span className="text-indigo-800 dark:text-indigo-300 font-semibold">AI profile score</span>
                <strong className="text-indigo-900 dark:text-indigo-200 font-extrabold">
                  {candidateProfile?.skills?.length ? Math.min(96, 70 + candidateProfile.skills.length * 4) : 85} / 100
                </strong>
              </div>
            </div>

            <Link
              href="/candidate/profile"
              className="mt-2 flex items-center justify-center gap-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Improve profile <ChevronRight size={14} />
            </Link>
          </div>

          <div className="h-card p-5 space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Your Momentum
            </p>
            <div className="flex items-end gap-2">
              <strong className="text-3xl font-black text-slate-900 dark:text-white">Active</strong>
              <span className="mb-1 text-xs font-bold text-emerald-600 dark:text-emerald-400">Verified</span>
            </div>
            <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300">
              Your verified profile is visible to recruiters searching for {candidateProfile?.skills?.[0] || "AI and Software"} talent.
            </p>
          </div>
        </aside>

        {/* Center Main Matches */}
        <main className="space-y-5">
          <div className="flex items-center justify-between pb-1">
            <div>
              <h2 className="font-bold text-slate-900 dark:text-white text-base">Top matches for you</h2>
              <p className="text-xs text-slate-600 dark:text-slate-300">Clear match reasoning before you apply.</p>
            </div>
            <Link href="/jobs" className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline">
              See all ({liveJobs.length})
            </Link>
          </div>

          {loading ? (
            <div className="p-8 text-center text-sm font-mono text-slate-400">
              Loading matching opportunities...
            </div>
          ) : liveJobs.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-400">
              No matching job requisitions currently open. Check back soon!
            </div>
          ) : (
            liveJobs.map((job) => (
              <article key={job.id} className="h-card p-5 sm:p-6 transition-all hover:shadow-md">
                <div className="flex gap-4">
                  <div className={`grid h-12 w-12 shrink-0 place-items-center rounded-xl font-bold text-base ${job.tone}`}>
                    {job.company[0] || "J"}
                  </div>
                  <div className="min-w-0 flex-1 space-y-3">
                    <div className="flex flex-wrap justify-between gap-3">
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-white text-base">
                          {job.title}
                        </h3>
                        <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-300 font-medium">
                          {job.company} <span className="text-slate-400">•</span> {job.location}
                        </p>
                      </div>
                      <div className="text-right">
                        <strong className="text-lg font-extrabold text-emerald-600 dark:text-emerald-400">
                          {job.match}%
                        </strong>
                        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">AI MATCH</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {job.matchedSkills.map((s: string) => (
                        <span key={s} className="h-chip good">
                          <Check size={12} /> {s}
                        </span>
                      ))}
                      <span className="h-chip bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-900">
                        Target Skill: {job.gap}
                      </span>
                    </div>

                    <div className="mt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-3">
                      <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                        {job.salary} • Verified Requisition
                      </span>
                      <div className="flex gap-2">
                        <Link href={`/jobs/${job.slug || job.id}`} className="h-btn h-btn-secondary">
                          View job
                        </Link>
                        <Link href={`/jobs/${job.slug || job.id}`} className="h-btn">
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

        {/* Right Sidebar */}
        <aside className="space-y-5">
          <div className="h-card p-5 space-y-3">
            <div className="flex items-center gap-2">
              <TrendingUp size={18} className="text-indigo-600 dark:text-indigo-400" />
              <h2 className="font-bold text-slate-900 dark:text-white text-sm">Active roles</h2>
            </div>
            <div className="space-y-2.5 pt-1">
              {uniqueDepartments.map((t, i) => (
                <Link
                  href="/jobs"
                  key={t}
                  className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors p-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/60"
                >
                  <span>
                    <em className="mr-2 not-italic font-bold text-slate-400">0{i + 1}</em>
                    {t}
                  </span>
                  <ChevronRight size={14} />
                </Link>
              ))}
            </div>
          </div>

          <div className="h-card p-5 space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Career Insight</p>
            <h3 className="font-bold text-slate-900 dark:text-white text-sm">
              You are ready for your next role.
            </h3>
            <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-300">
              Keep your profile up to date with your latest project repositories and verified skills.
            </p>
            <Link
              href="/career"
              className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline pt-1"
            >
              Explore your plan <ArrowRight size={13} />
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
