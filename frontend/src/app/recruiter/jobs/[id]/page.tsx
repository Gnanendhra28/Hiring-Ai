"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function RecruiterJobDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [verificationStatus, setVerificationStatus] = useState<"DRAFT" | "PENDING_VERIFICATION" | "APPROVED" | "REJECTED">("DRAFT");
  const [publicationStatus, setPublicationStatus] = useState<"DRAFT" | "PUBLISHED" | "PAUSED" | "CLOSED">("DRAFT");
  const [rejectionReason] = useState<string | null>(null);

  const handleSubmitVerification = () => {
    setVerificationStatus("PENDING_VERIFICATION");
  };

  const handlePublish = () => {
    if (verificationStatus !== "APPROVED") return;
    setPublicationStatus("PUBLISHED");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        <Link href="/recruiter/jobs" className="text-xs text-blue-400 hover:underline">
          &larr; Back to Job Requisitions
        </Link>

        {/* Job Header & Verification Status */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Engineering Department</span>
                <span className="text-slate-600">&bull;</span>
                {/* Verification Badge */}
                {verificationStatus === "DRAFT" && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                    Verification: DRAFT
                  </span>
                )}
                {verificationStatus === "PENDING_VERIFICATION" && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Verification: PENDING ADMIN REVIEW
                  </span>
                )}
                {verificationStatus === "APPROVED" && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Verification: APPROVED
                  </span>
                )}
                {verificationStatus === "REJECTED" && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    Verification: REJECTED
                  </span>
                )}
              </div>

              <h1 className="text-3xl font-bold text-white mt-2">Staff Backend Engineer - Python</h1>
              <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
                <span>📍 Remote / Austin, TX</span>
                <span>💼 FULL_TIME</span>
                <span>🏷️ ID: {id}</span>
                <span>Publication: <strong className="text-slate-200">{publicationStatus}</strong></span>
              </div>
            </div>

            {/* Verification & Publication Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              {verificationStatus === "DRAFT" || verificationStatus === "REJECTED" ? (
                <button
                  onClick={handleSubmitVerification}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all"
                >
                  Submit for Admin Verification &rarr;
                </button>
              ) : null}

              {verificationStatus === "APPROVED" && publicationStatus !== "PUBLISHED" ? (
                <button
                  onClick={handlePublish}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all"
                >
                  Publish Requisition
                </button>
              ) : null}

              {verificationStatus !== "APPROVED" && (
                <button
                  disabled
                  title="Job posting must be approved by Platform Admin before publication."
                  className="px-4 py-2 bg-slate-800/50 text-slate-500 rounded-lg text-xs font-semibold cursor-not-allowed border border-slate-800"
                >
                  Publish (Verification Required)
                </button>
              )}
            </div>
          </div>

          {/* Admin Rejection Reason Alert Box */}
          {verificationStatus === "REJECTED" && rejectionReason && (
            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs p-4 rounded-xl space-y-1">
              <div className="font-bold text-rose-400">Admin Rejection Feedback</div>
              <p>{rejectionReason}</p>
              <div className="text-[11px] text-slate-400 pt-1">Please edit the job description above and resubmit for verification.</div>
            </div>
          )}

          {/* Requisition Navigation Tabs */}
          <div className="flex border-b border-slate-800 space-x-6 text-xs font-semibold">
            <span className="text-blue-400 border-b-2 border-blue-400 pb-3">Job Details</span>
            <Link href={`/recruiter/jobs/${id}/intelligence`} className="text-slate-400 hover:text-slate-200 pb-3">
              AI Intelligence & Requirements &rarr;
            </Link>
            <Link href={`/recruiter/jobs/${id}/applications`} className="text-slate-400 hover:text-slate-200 pb-3">
              Candidate Applications Pipeline &rarr;
            </Link>
          </div>


          {/* Job Specifications */}
          <div className="space-y-4 text-xs leading-relaxed text-slate-300 pt-2">
            <h3 className="text-sm font-semibold text-white">Job Description & Requisition Brief</h3>
            <p>
              Architecting high-scale distributed backend services using Python 3.13, FastAPI, and PostgreSQL pgvector.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
