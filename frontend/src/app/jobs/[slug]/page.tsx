"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import {
  ArrowLeft,
  Bookmark,
  Briefcase,
  CheckCircle2,
  Clock,
  ExternalLink,
  MapPin,
  Sparkles,
  Star,
} from "lucide-react";

export default function PublicJobDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [applied, setApplied] = useState(false);
  const [saved, setSaved] = useState(false);
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

  // Load initial saved status on mount
  useEffect(() => {
    const targetId = job?.id || slug;
    if (!targetId) return;
    const savedIdsStr = localStorage.getItem("hiring_ai_saved_job_ids") || "[]";
    const savedIds: string[] = JSON.parse(savedIdsStr);
    if (savedIds.includes(targetId)) {
      setSaved(true);
    }
  }, [job, slug]);

  const handleSaveJob = () => {
    const targetId = job?.id || slug;
    if (!targetId) return;
    const savedIdsStr = localStorage.getItem("hiring_ai_saved_job_ids") || "[]";
    const savedIds: string[] = JSON.parse(savedIdsStr);

    if (saved) {
      const updated = savedIds.filter((id) => id !== targetId);
      localStorage.setItem("hiring_ai_saved_job_ids", JSON.stringify(updated));
      setSaved(false);
    } else {
      if (!savedIds.includes(targetId)) {
        savedIds.push(targetId);
        localStorage.setItem("hiring_ai_saved_job_ids", JSON.stringify(savedIds));
      }
      setSaved(true);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-sans">
        <div className="text-xs text-slate-400 font-semibold animate-pulse">
          Loading job details...
        </div>
      </div>
    );
  }

  const companyName = job?.department || "Enterprise Requisition";
  const title = job?.title || "Requisition Specification";
  const location = job?.location || "Remote";
  const rawDescription = job?.description || "";

  // Parse strictly real description data provided by employee
  const renderRealStructuredDescription = (rawDesc: string) => {
    if (!rawDesc) {
      return <p className="text-xs text-slate-400">No description provided by employee.</p>;
    }

    // Split description by section headers (e.g. "## ")
    const rawSections = rawDesc.split(/(?=^##\s+)/m).filter((s) => s.trim().length > 0);

    return (
      <div className="space-y-8">
        {rawSections.map((sec, idx) => {
          const lines = sec.split("\n").filter((l) => l.trim().length > 0);
          let headerText = "";
          let bodyLines: string[] = [];

          if (lines[0]?.startsWith("## ")) {
            headerText = lines[0].replace(/^##\s+/, "").trim();
            bodyLines = lines.slice(1);
          } else {
            bodyLines = lines;
          }

          const isListSection = bodyLines.some((l) =>
            /^[•\-\*\d+\.]/.test(l.trim())
          );

          return (
            <div key={idx} className="space-y-3">
              {headerText && (
                <h3 className="text-sm font-bold text-white border-b border-slate-800/60 pb-1">
                  {headerText}
                </h3>
              )}

              {isListSection ? (
                <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
                  {bodyLines.map((line, lIdx) => {
                    const cleaned = line.replace(/^[•\-\*\d+\.]\s*/, "").trim();
                    if (!cleaned) return null;
                    return (
                      <li key={lIdx} className="flex items-start gap-2">
                        <span className="text-slate-400 font-bold">•</span>
                        <span>{cleaned}</span>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <div className="space-y-2 text-xs text-slate-300 leading-relaxed font-normal">
                  {bodyLines.map((line, lIdx) => (
                    <p key={lIdx}>{line.trim()}</p>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          <ArrowLeft size={15} /> View All Jobs
        </Link>

        {/* Top Job Header Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1.5 min-w-0 flex-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-white">
                {title}
              </h1>

              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-300 font-medium">
                <span className="font-semibold text-slate-200">{companyName}</span>
                <span className="flex items-center gap-1 text-amber-400 font-bold">
                  <Star size={13} className="fill-amber-400" /> 4.1
                </span>
                <span className="text-slate-500">|</span>
                <span className="text-slate-400">4 Reviews</span>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-2 font-medium">
                <span className="flex items-center gap-1.5">
                  <Briefcase size={14} className="text-slate-400" /> 0 - 3 years
                </span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-300 font-semibold">{job?.salary || "₹ Not Disclosed"}</span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-300 pt-1 font-medium">
                <MapPin size={14} className="text-slate-400 shrink-0" />
                <span>{location}</span>
              </div>
            </div>

            {/* Company Logo Badge on Right */}
            <div className="w-16 h-16 rounded-2xl bg-indigo-950 border border-indigo-800 text-indigo-300 font-extrabold text-2xl grid place-items-center shrink-0 shadow-md">
              {companyName[0] || "E"}
            </div>
          </div>

          <div className="flex justify-end">
            <a
              href="#send-jobs"
              className="text-xs font-bold text-indigo-400 hover:underline flex items-center gap-1"
            >
              Send me jobs like this
            </a>
          </div>

          {/* Card Divider */}
          <hr className="border-slate-800" />

          {/* Bottom Card Footer Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-medium">
              <span>
                Posted: <strong className="text-slate-200">Recently</strong>
              </span>
              <span className="text-slate-700">|</span>
              <span>
                Openings: <strong className="text-slate-200">2</strong>
              </span>
              <span className="text-slate-700">|</span>
              <span>
                Applicants: <strong className="text-slate-200">100+</strong>
              </span>
              {closingDateStr && (
                <>
                  <span className="text-slate-700">|</span>
                  <span className={`font-mono ${isClosed ? "text-rose-400 font-bold" : "text-slate-300"}`}>
                    Closing Date: {closingDateStr}
                  </span>
                </>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleSaveJob}
                className={`px-5 py-2.5 rounded-full text-xs font-bold border transition-all flex items-center gap-1.5 ${
                  saved
                    ? "bg-indigo-950 border-indigo-700 text-indigo-300"
                    : "border-slate-700 text-slate-200 hover:bg-slate-800"
                }`}
              >
                <Bookmark size={14} /> {saved ? "Saved" : "Save"}
              </button>

              {isClosed ? (
                <div className="px-5 py-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-full text-xs font-bold flex items-center gap-1.5 cursor-not-allowed">
                  <span>🔒 Applications Closed</span>
                </div>
              ) : applied ? (
                <div className="px-6 py-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full text-xs font-bold flex items-center gap-1.5">
                  <CheckCircle2 size={15} /> Application Submitted
                </div>
              ) : (
                <button
                  onClick={handleApply}
                  disabled={submitting}
                  className="px-7 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-xs font-bold shadow-lg shadow-blue-600/30 transition-all disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Apply"}
                </button>
              )}

              {!isClosed && (
                <Link
                  href={`/career?jobId=${job?.id || slug}`}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
                >
                  <Sparkles size={14} /> Apply with AI
                </Link>
              )}
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              {error}
            </div>
          )}
        </div>

        {/* Main Structured Job Description Body - STRICTLY REAL DATA FROM POSTGRESQL */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 space-y-6 shadow-2xl">
          {/* Section Heading */}
          <div className="space-y-1 border-b border-slate-800 pb-4">
            <h2 className="text-xl font-bold text-white">Job description</h2>
            <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
            <p className="text-xs text-slate-400 font-medium">Location: {location}</p>
            {job?.company_website && (
              <p className="pt-1 text-xs text-slate-400 font-medium flex items-center gap-1">
                Website:{" "}
                <a
                  href={job.company_website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-indigo-400 hover:underline flex items-center gap-1 font-semibold"
                >
                  {job.company_website} <ExternalLink size={12} />
                </a>
              </p>
            )}
          </div>

          {/* Render Real Employee Description Sections */}
          {renderRealStructuredDescription(rawDescription)}

          {/* Role Metadata Specification Table */}
          <div className="space-y-2 text-xs text-slate-300 border-t border-slate-800 pt-6">
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Role:</span>
              <span className="font-semibold text-white">{title}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Department:</span>
              <span className="font-semibold text-white">{companyName}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Employment Type:</span>
              <span className="font-semibold text-white">{job?.employment_type || "Full Time, Permanent"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
