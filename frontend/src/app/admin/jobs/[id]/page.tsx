"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function AdminJobDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [decision, setDecision] = useState<"APPROVED" | "REJECTED" | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);

  const handleApprove = () => {
    setDecision("APPROVED");
  };

  const handleConfirmReject = () => {
    if (!rejectionReason.trim()) return;
    setDecision("REJECTED");
    setShowRejectModal(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link href="/admin/jobs" className="text-xs text-slate-400 hover:underline">
          &larr; Back to Verification Queue
        </Link>

        {/* Verification Status Banner */}
        {decision === "APPROVED" && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs p-4 rounded-xl flex items-center justify-between">
            <div>
              <span className="font-bold">✓ Job Posting Approved</span> &bull; The recruiter organization can now publish this position to the public directory.
            </div>
          </div>
        )}

        {decision === "REJECTED" && (
          <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs p-4 rounded-xl">
            <span className="font-bold">✕ Job Posting Rejected</span> &bull; Reason: {rejectionReason}
          </div>
        )}

        {/* Job Detail Specification Card */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div>
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Acme AI Systems &bull; Requisition Verification</span>
              <h1 className="text-3xl font-bold text-white mt-1">Staff Backend Engineer - Python</h1>
              <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
                <span>📍 Remote / Austin, TX</span>
                <span>💼 FULL_TIME</span>
                <span>🏷️ Requisition ID: {id}</span>
              </div>
            </div>

            {decision === null && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowRejectModal(true)}
                  className="px-4 py-2 bg-rose-600/20 border border-rose-500/30 hover:bg-rose-600/30 text-rose-300 text-xs font-semibold rounded-lg transition-all"
                >
                  Reject Requisition
                </button>
                <button
                  onClick={handleApprove}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-md transition-all"
                >
                  Approve Requisition
                </button>
              </div>
            )}
          </div>

          <div className="space-y-4 text-xs leading-relaxed text-slate-300">
            <h3 className="text-sm font-semibold text-white">Requisition Specification & Description</h3>
            <p>
              Architecting high-scale distributed backend services using Python 3.13, FastAPI, and PostgreSQL pgvector.
            </p>

            <h3 className="text-sm font-semibold text-white pt-2">Compliance Check Points</h3>
            <ul className="list-disc list-inside space-y-1 text-slate-400">
              <li>Verified valid employment type and non-discriminatory location criteria.</li>
              <li>Clear responsibilities and technical qualifications defined.</li>
              <li>Recruiter membership verified under active organization tenant.</li>
            </ul>
          </div>
        </div>

        {/* Rejection Reason Modal */}
        {showRejectModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-lg w-full space-y-4">
              <h3 className="text-lg font-bold text-white">Reject Requisition</h3>
              <p className="text-xs text-slate-400">
                Please provide a mandatory rejection reason explaining what the recruiter needs to update before resubmitting.
              </p>
              <textarea
                rows={4}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Job description is too brief. Please add specific responsibilities and qualifications."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-rose-500"
              />
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setShowRejectModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-md"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmReject}
                  disabled={!rejectionReason.trim()}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-md transition-all disabled:opacity-50"
                >
                  Confirm Rejection
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
