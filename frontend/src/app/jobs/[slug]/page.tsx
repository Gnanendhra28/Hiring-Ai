"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import {
  ArrowLeft,
  Briefcase,
  CheckCircle2,
  Clock,
  FileText,
  MapPin,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";

export default function PublicJobDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [applied, setApplied] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchJob() {
      if (!slug) return;
      try {
        const res = await apiFetch(`/api/v1/jobs/${slug}`);
        if (res.ok) {
          const data = await res.json();
          setJob(data);
        }
      } catch (err) {
        console.error("Error fetching job:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchJob();
  }, [slug]);

  // Determine if application closing date has passed
  const parseClosingDate = () => {
    if (!job?.description) return { dateStr: null, isClosed: false };
    const match = job.description.match(/Application Closing Date\*\*: ([^\n]+)/);
    if (!match || !match[1]) return { dateStr: null, isClosed: false };

    const raw = match[1].trim();
    let closingDt: Date | null = null;

    if (raw.includes("-")) {
      closingDt = new Date(raw);
    } else if (raw.includes("/")) {
      const parts = raw.split("/");
      if (parts.length === 3) {
        closingDt = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
      }
    }

    if (closingDt && !isNaN(closingDt.getTime())) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return { dateStr: raw, isClosed: today > closingDt };
    }

    return { dateStr: raw, isClosed: false };
  };

  const { dateStr: closingDateStr, isClosed: isDateExpired } = parseClosingDate();
  const isClosed = isDateExpired || job?.status === "CLOSED";

  const handleApply = async () => {
    if (isClosed) return;
    setSubmitting(true);
    setError(null);

    try {
      if (job?.id) {
        const res = await apiFetch("/api/v1/candidate/applications", {
          method: "POST",
          body: JSON.stringify({ job_id: job.id }),
        });
        if (res.ok) {
          setApplied(true);
        } else {
          const errData = await res.json().catch(() => ({ detail: null }));
          throw new Error(errData.detail || "Failed to submit application.");
        }
      } else {
        setApplied(true);
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit application.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-sans">
        <div className="text-xs text-slate-400 font-semibold animate-pulse">
          Loading job requisition details...
        </div>
      </div>
    );
  }

  // Format job description into structured sections
  const renderStructuredDescription = (rawDesc: string) => {
    if (!rawDesc) return <p className="text-slate-400">No description provided.</p>;

    const lines = rawDesc.split("\n").filter((l) => l.trim().length > 0);

    return (
      <div className="space-y-6">
        {/* Section 1: Overview */}
        <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
            <FileText size={16} /> Role Overview &amp; Summary
          </div>
          <p className="text-xs text-slate-200 leading-relaxed font-medium">
            {lines[0] || "We are seeking an outstanding engineer to join our high-impact AI team."}
          </p>
        </div>

        {/* Section 2: Key Responsibilities */}
        <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
            <Target size={16} /> Key Responsibilities &amp; Core Scope
          </div>
          <ul className="space-y-2 text-xs text-slate-300">
            <li className="flex items-start gap-2">
              <span className="text-indigo-400 font-bold">•</span>
              <span>Design, build, and maintain production AI microservices and scalable REST APIs.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-400 font-bold">•</span>
              <span>Architect vector embedding database pipelines (PGVector, HNSW) for real-time search.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-400 font-bold">•</span>
              <span>Collaborate with cross-functional talent acquisition and platform engineering teams.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-indigo-400 font-bold">•</span>
              <span>Enforce high test coverage, robust async code, and automated CI/CD container deployments.</span>
            </li>
          </ul>
        </div>

        {/* Section 3: Technical Requirements */}
        <div className="p-5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <Zap size={16} /> Technical Qualifications &amp; Stack
          </div>
          <div className="flex flex-wrap gap-2">
            {["Python 3.13", "FastAPI", "Generative AI", "RAG Systems", "PostgreSQL", "Docker", "Git Workflows"].map((skill) => (
              <span
                key={skill}
                className="px-3 py-1 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs font-semibold flex items-center gap-1.5"
              >
                <CheckCircle2 size={13} /> {skill}
              </span>
            ))}
          </div>
        </div>

        {/* Full Original Description Text */}
        <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Full Specification Details
          </div>
          <div className="whitespace-pre-line text-xs font-mono text-slate-300 leading-relaxed pt-1">
            {rawDesc}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 sm:p-10 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          <ArrowLeft size={15} /> View All Jobs
        </Link>

        {/* Job Header */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-2xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-slate-800 pb-6">
            <div className="space-y-2">
              <span className="px-3 py-1 rounded-lg bg-indigo-950 text-indigo-300 border border-indigo-800 text-xs font-extrabold uppercase tracking-wider">
                {job?.department || "Engineering Requisition"}
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                {job?.title || "Requisition Specification"}
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-1 font-medium">
                <span className="flex items-center gap-1">
                  <MapPin size={14} className="text-indigo-400" /> {job?.location || "Remote"}
                </span>
                <span className="flex items-center gap-1">
                  <Briefcase size={14} className="text-indigo-400" /> {job?.employment_type || "FULL_TIME"}
                </span>
                {closingDateStr && (
                  <span className={`flex items-center gap-1 font-mono ${isClosed ? "text-rose-400 font-bold" : "text-slate-300"}`}>
                    <Clock size={14} /> Closing Date: {closingDateStr}
                  </span>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              {isClosed ? (
                <div className="px-5 py-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-xs font-bold flex items-center gap-1.5 cursor-not-allowed">
                  <span>🔒 Applications Closed</span>
                </div>
              ) : (
                <>
                  {applied ? (
                    <div className="px-5 py-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl text-xs font-bold flex items-center gap-1.5">
                      <CheckCircle2 size={15} /> Application Submitted
                    </div>
                  ) : (
                    <button
                      onClick={handleApply}
                      disabled={submitting}
                      className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 rounded-xl text-xs font-bold transition-all disabled:opacity-50"
                    >
                      {submitting ? "Submitting..." : "Apply Position"}
                    </button>
                  )}

                  <Link
                    href={`/career?jobId=${job?.id || slug}`}
                    className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
                  >
                    <Sparkles size={15} /> Apply with AI
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Closed Banner Warning */}
          {isClosed && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="text-rose-400 font-bold">ℹ</span>
                <span>
                  Applications Closed: The application closing date ({closingDateStr || "deadline"}) for this position has passed.
                </span>
              </span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              {error}
            </div>
          )}

          {/* Structured Job Specifications */}
          <div className="space-y-4 pt-2">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Structured Job Description &amp; Specifications
            </h2>
            {renderStructuredDescription(job?.description)}
          </div>
        </div>
      </div>
    </div>
  );
}
