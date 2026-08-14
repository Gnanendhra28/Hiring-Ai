"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface CommItem {
  id: string;
  recipient_email: string;
  workflow_stage: string;
  subject: string;
  status: "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "SENT" | "CANCELLED";
  created_at: string;
}

export default function RecruiterCommunicationsPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [comms, setComms] = useState<CommItem[]>([
    {
      id: "comm-1",
      recipient_email: "candidate@example.com",
      workflow_stage: "INTERVIEW_INVITATION",
      subject: "Invitation to Technical Interview - Acme AI Systems",
      status: "PENDING_APPROVAL",
      created_at: "2026-08-14T14:00:00Z",
    },
  ]);

  const handleApprove = (id: string) => {
    setComms(
      comms.map((c) => (c.id === id ? { ...c, status: "APPROVED" as const } : c))
    );
  };

  const handleSend = (id: string) => {
    setComms(
      comms.map((c) => (c.id === id ? { ...c, status: "SENT" as const } : c))
    );
  };

  const handleCancel = (id: string) => {
    setComms(
      comms.map((c) => (c.id === id ? { ...c, status: "CANCELLED" as const } : c))
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Job Requisition
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Human Email Approval Queue</h1>
            <p className="text-slate-400 text-xs">Review, validate, and explicitly approve hiring communications before delivery.</p>
          </div>
        </div>

        {/* Email Approval Queue Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                <th className="p-4">Recipient</th>
                <th className="p-4">Stage</th>
                <th className="p-4">Subject</th>
                <th className="p-4">Approval Status</th>
                <th className="p-4 text-right">Human Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {comms.map((c) => (
                <tr key={c.id} className="hover:bg-slate-900/50">
                  <td className="p-4 font-semibold text-white">{c.recipient_email}</td>
                  <td className="p-4 text-slate-300">{c.workflow_stage}</td>
                  <td className="p-4 text-slate-300 max-w-xs truncate">{c.subject}</td>
                  <td className="p-4">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold border ${
                      c.status === "APPROVED"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : c.status === "SENT"
                        ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                        : c.status === "CANCELLED"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    }`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="p-4 text-right space-x-2">
                    {c.status === "PENDING_APPROVAL" && (
                      <>
                        <button
                          onClick={() => handleCancel(c.id)}
                          className="px-2.5 py-1 bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 border border-rose-500/30 rounded text-[11px] font-medium"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleApprove(c.id)}
                          className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-semibold shadow-md"
                        >
                          Approve Email
                        </button>
                      </>
                    )}

                    {c.status === "APPROVED" && (
                      <button
                        onClick={() => handleSend(c.id)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold shadow-md"
                      >
                        Send Email Now &rarr;
                      </button>
                    )}

                    {c.status === "SENT" && (
                      <span className="text-[11px] text-slate-500 font-mono">Delivered ✓</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
