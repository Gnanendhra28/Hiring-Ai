"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function PublicJobDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [applied, setApplied] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleApply = async () => {
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setApplied(true);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link href="/jobs" className="text-xs text-blue-400 hover:underline">
          &larr; Back to Job Directory
        </Link>

        {/* Job Header */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div>
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Acme AI Systems</span>
              <h1 className="text-3xl font-bold text-white mt-1">Staff Backend Engineer - Python</h1>
              <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
                <span>📍 Remote / Austin, TX</span>
                <span>💼 FULL_TIME</span>
                <span>🏷️ Slug: {slug}</span>
              </div>
            </div>

            <div>
              {applied ? (
                <div className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-xs font-semibold">
                  ✓ Application Submitted
                </div>
              ) : (
                <button
                  onClick={handleApply}
                  disabled={submitting}
                  className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all"
                >
                  {submitting ? "Submitting..." : "Apply for Position"}
                </button>
              )}
            </div>
          </div>

          {/* Job Specifications */}
          <div className="space-y-4 text-xs leading-relaxed text-slate-300 pt-4">
            <h3 className="text-sm font-semibold text-white">About the Role</h3>
            <p>
              We are seeking an exceptional Staff Backend Engineer to join our core architecture team. You will lead the design and implementation of highly-scalable Python 3.13 microservices, PostgreSQL 16 vector databases, and real-time event streaming systems.
            </p>

            <h3 className="text-sm font-semibold text-white pt-2">Key Requirements</h3>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li>7+ years experience with Python backend frameworks (FastAPI / AsyncIO).</li>
              <li>Deep understanding of relational database optimization and vector similarity search.</li>
              <li>Experience with cloud-native multi-tenant SaaS architecture.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
