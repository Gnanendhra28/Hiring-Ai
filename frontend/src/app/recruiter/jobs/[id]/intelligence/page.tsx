"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface JobRequirementUI {
  id: string;
  requirement_type: string;
  raw_value: string;
  canonical_value: string;

  requirement_level: "REQUIRED" | "PREFERRED" | "INFORMATIONAL";
  hard_constraint: boolean;
  operator?: string;
  minimum_value?: number;
  unit?: string;
  priority: string;
  confidence: number;
  evidence_text?: string;
  evidence_verification_status: "VERIFIED" | "PARTIALLY_VERIFIED" | "UNVERIFIED";
  is_protected_feature: boolean;
}

export default function JobIntelligencePage() {
  const params = useParams();
  const id = params?.id as string;

  const [activeVersion] = useState({
    version_number: 1,
    status: "COMPLETED",
    overall_confidence: 0.94,
    ai_provider: "OPENAI",
    model_name: "gpt-4o-mini",
  });

  const [requirements] = useState<JobRequirementUI[]>([
    {
      id: "1",
      requirement_type: "SKILL",
      raw_value: "Python 3.13",
      canonical_value: "Python",
      requirement_level: "REQUIRED",
      hard_constraint: true,
      priority: "CRITICAL",
      confidence: 0.98,
      evidence_text: "Must have 3+ years of Python development experience.",
      evidence_verification_status: "VERIFIED",
      is_protected_feature: false,
    },
    {
      id: "2",
      requirement_type: "EXPERIENCE",
      raw_value: "3+ years of backend development",
      canonical_value: "36 Months Experience",
      requirement_level: "REQUIRED",
      hard_constraint: true,
      operator: "GTE",
      minimum_value: 36,
      unit: "MONTHS",
      priority: "CRITICAL",
      confidence: 0.95,
      evidence_text: "Must have 3+ years of Python development experience.",
      evidence_verification_status: "VERIFIED",
      is_protected_feature: false,
    },
    {
      id: "3",
      requirement_type: "SKILL",
      raw_value: "Retrieval Augmented Generation",
      canonical_value: "RAG",
      requirement_level: "PREFERRED",
      hard_constraint: false,
      priority: "MEDIUM",
      confidence: 0.92,
      evidence_text: "Experience building Retrieval Augmented Generation applications is preferred.",
      evidence_verification_status: "VERIFIED",
      is_protected_feature: false,
    },
    {
      id: "4",
      requirement_type: "WORK_MODE",
      raw_value: "Hybrid - 3 days in office",
      canonical_value: "HYBRID",
      requirement_level: "REQUIRED",
      hard_constraint: true,
      priority: "HIGH",
      confidence: 0.96,
      evidence_text: "Hybrid role working 3 days in office.",
      evidence_verification_status: "VERIFIED",
      is_protected_feature: false,
    },
  ]);

  const [responsibilities] = useState<string[]>([
    "Build and optimize high-throughput RAG search pipelines.",
    "Architect multi-tenant FastAPI backend microservices with pgvector embeddings.",
  ]);

  const [intents] = useState<string[]>([
    "Production AI & Vector Search Engineering",
  ]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-6">
        <Link href={`/recruiter/jobs/${id}`} className="text-xs text-blue-400 hover:underline">
          &larr; Back to Job Requisition
        </Link>

        {/* Intelligence Header */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">AI Job Intelligence</span>
                <span className="text-slate-600">&bull;</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Version {activeVersion.version_number} &bull; ACTIVE
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  Confidence: {Math.round(activeVersion.overall_confidence * 100)}% (HIGH)
                </span>
              </div>
              <h1 className="text-2xl font-bold text-white mt-2">Structured Requirements & Intent Engine</h1>
              <p className="text-xs text-slate-400 mt-1">
                Extracted via {activeVersion.ai_provider} {activeVersion.model_name} with pgvector HNSW embeddings.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all"
              >
                Regenerate Intelligence
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 space-x-6 text-xs font-semibold">
            <Link href={`/recruiter/jobs/${id}`} className="text-slate-400 hover:text-slate-200 pb-3">
              Job Details
            </Link>
            <span className="text-purple-400 border-b-2 border-purple-400 pb-3">
              AI Intelligence & Requirements
            </span>
            <Link href={`/recruiter/jobs/${id}/applications`} className="text-slate-400 hover:text-slate-200 pb-3">
              Candidate Applications Pipeline &rarr;
            </Link>
          </div>

          {/* Requirements Grid */}
          <div className="space-y-6 pt-2">
            <h2 className="text-sm font-semibold text-white">Extracted & Structured Job Requirements</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {requirements.map((req) => (
                <div key={req.id} className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {req.requirement_type}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {req.requirement_level === "REQUIRED" ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          REQUIRED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                          PREFERRED
                        </span>
                      )}
                      {req.hard_constraint ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          HARD CONSTRAINT
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">
                          SOFT PREFERENCE
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-white">{req.raw_value}</h3>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Canonical: <strong className="text-blue-400">{req.canonical_value}</strong>
                    </div>
                  </div>

                  {req.operator && (
                    <div className="text-xs bg-slate-900/80 p-2 rounded border border-slate-800 text-slate-300">
                      Numeric Constraint: <strong>{req.operator} {req.minimum_value} {req.unit}</strong>
                    </div>
                  )}

                  {req.evidence_text && (
                    <div className="text-[11px] text-slate-400 bg-slate-900/40 p-2.5 rounded border border-slate-800/80">
                      <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                        <span>Evidence Quote</span>
                        <span className="text-emerald-400 font-semibold">✓ VERIFIED</span>
                      </div>
                      &ldquo;{req.evidence_text}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Responsibilities & Intent */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Responsibilities</h3>
                <ul className="space-y-2 text-xs text-slate-300 list-disc list-inside">
                  {responsibilities.map((resp, i) => (
                    <li key={i}>{resp}</li>
                  ))}
                </ul>
              </div>

              <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-5 space-y-3">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Role Intent</h3>
                <div className="space-y-2 text-xs text-slate-300">
                  {intents.map((intent, i) => (
                    <div key={i} className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-300 font-medium">
                      🎯 {intent}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
