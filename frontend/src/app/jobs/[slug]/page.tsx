"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link href="/jobs" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
          &larr; Back to Job Directory
        </Link>

        {/* Job Header */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 space-y-4 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div>
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                {job?.department || "Engineering Requisition"}
              </span>
              <h1 className="text-3xl font-bold text-white mt-1">
                {job?.title || "Requisition Specification"}
              </h1>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-2">
                <span>📍 {job?.location || "Remote"}</span>
                <span>💼 {job?.employment_type || "FULL_TIME"}</span>
                {closingDateStr && (
                  <span className={`font-mono ${isClosed ? "text-rose-400 font-bold" : "text-slate-300"}`}>
                    📅 Closing Date: {closingDateStr}
                  </span>
                )}
              </div>
            </div>

            <div>
              {isClosed ? (
                <div className="px-5 py-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-lg text-xs font-bold flex items-center gap-1.5 cursor-not-allowed">
                  <span>🔒 Applications Closed</span>
                </div>
              ) : applied ? (
                <div className="px-5 py-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-bold flex items-center gap-1.5">
                  <span>✓ Application Submitted</span>
                </div>
              ) : (
                <button
                  onClick={handleApply}
                  disabled={submitting}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Apply for Position"}
                </button>
              )}
            </div>
          </div>

          {/* Closed Banner Warning */}
          {isClosed && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="text-rose-400 font-bold">ℹ</span>
                <span>
                  Applications Closed: The application closing date ({closingDateStr || "deadline"}) for this position has passed. No further applications will be accepted.
                </span>
              </span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              {error}
            </div>
          )}

          {/* Job Specifications */}
          <div className="space-y-4 text-xs leading-relaxed text-slate-300 pt-4">
            <h3 className="text-sm font-semibold text-white">Requisition Specification &amp; Description</h3>
            <div className="whitespace-pre-line font-mono text-slate-300 bg-slate-950/60 p-4 rounded-lg border border-slate-800 leading-relaxed">
              {job?.description || "No description provided."}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
