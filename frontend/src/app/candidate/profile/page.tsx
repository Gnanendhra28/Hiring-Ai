"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth/AuthContext";

export default function CandidateProfilePage() {
  const { user } = useAuth();

  const [headline, setHeadline] = useState("Senior Full Stack & AI Systems Engineer");
  const [location, setLocation] = useState("San Francisco, CA");
  const [phoneNumber, setPhoneNumber] = useState("+91 98765 43210");
  const [college, setCollege] = useState("Stanford University");
  const [skills, setSkills] = useState("React, Next.js, TypeScript, FastAPI, Python, PostgreSQL, Vector Search");
  const [summary, setSummary] = useState(
    "Senior software engineer with 6+ years of experience building high-scale distributed web applications, AI vector search pipelines, and modern frontend design systems."
  );
  const [saved, setSaved] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono mb-2">
            <span>CANDIDATE PROFILE</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Professional Profile</h1>
          <p className="text-slate-400 text-xs mt-1">Manage your professional identity, academic credentials, and skill vector attributes.</p>
        </div>

        <Link
          href="/candidate/dashboard"
          className="text-xs font-mono text-slate-400 hover:text-white hover:underline self-start sm:self-auto"
        >
          ← Return to Dashboard
        </Link>
      </div>

      {saved && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center space-x-2">
          <span>✓</span>
          <span>Profile changes saved successfully!</span>
        </div>
      )}

      {/* Profile Form Card */}
      <form onSubmit={handleSubmit} className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-6 shadow-2xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              disabled
              value={user?.full_name || "Jane Candidate"}
              className="w-full px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 font-mono text-sm cursor-not-allowed"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              disabled
              value={user?.email || "candidate@example.com"}
              className="w-full px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 font-mono text-sm cursor-not-allowed"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
              Professional Headline
            </label>
            <input
              type="text"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="e.g. Senior Frontend Architect"
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
              Location
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. San Francisco, CA"
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono transition-all"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
              Phone Number
            </label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+91 XXXXX XXXXX"
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
              College / University
            </label>
            <input
              type="text"
              value={college}
              onChange={(e) => setCollege(e.target.value)}
              placeholder="e.g. Stanford University or IIT Bombay"
              className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
            Key Technical Skills (comma-separated)
          </label>
          <input
            type="text"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono transition-all"
          />
        </div>

        <div>
          <label className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
            Professional Summary &amp; Bio
          </label>
          <textarea
            rows={4}
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm font-mono transition-all"
          />
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-800">
          <button
            type="submit"
            className="py-3 px-6 rounded-xl btn-shimmer font-bold text-white shadow-lg shadow-sky-500/20 text-xs transition-all"
          >
            Save Profile Changes
          </button>
        </div>
      </form>
    </div>
  );
}
