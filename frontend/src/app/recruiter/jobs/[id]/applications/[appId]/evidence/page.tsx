"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface ExtractedSkill {
  id: string;
  raw_skill_name: string;
  canonical_skill_name: string;
  years_experience: number;
  confidence: number;
  evidence_text: string;
  page_number: number;
}

interface RequirementMatchUI {
  id: string;
  requirement_type: string;
  canonical_required_value: string;
  requirement_level: "REQUIRED" | "PREFERRED";
  hard_constraint: boolean;
  match_status: "MATCHED" | "PARTIALLY_MATCHED" | "NOT_MATCHED" | "UNKNOWN" | "PROTECTED_EXCLUDED";
  candidate_value?: string;
  confidence: number;
  reason?: string;
  evidence_text?: string;
}

interface SemanticMatchUI {
  id: string;
  query_context: string;
  candidate_context: string;
  similarity_score: number;
}

interface FactorScoreUI {
  id: string;
  factor_type: string;
  raw_score: number;
  configured_weight: number;
  normalized_weight: number;
  weighted_contribution: number;
  applicable: boolean;
  reason?: string;
}

export default function RecruiterApplicationEvidencePage() {
  const params = useParams();
  const jobId = params?.id as string;

  // Candidate Deterministic Score Data (Phase 9B)
  const [scoreData] = useState({
    overall_score: 87.4,
    eligibility_status: "PASS",
    score_confidence: 0.94,
    confidence_tier: "HIGH",
    calculated_at: "2026-08-14T16:45:00Z",
  });

  const [factorScores] = useState<FactorScoreUI[]>([
    {
      id: "fs-1",
      factor_type: "REQUIRED_SKILLS",
      raw_score: 90.0,
      configured_weight: 0.30,
      normalized_weight: 0.30,
      weighted_contribution: 27.0,
      applicable: true,
      reason: "2/2 required skills matched.",
    },
    {
      id: "fs-2",
      factor_type: "SEMANTIC_MATCH",
      raw_score: 85.0,
      configured_weight: 0.20,
      normalized_weight: 0.20,
      weighted_contribution: 17.0,
      applicable: true,
      reason: "Average pgvector context similarity 0.85.",
    },
    {
      id: "fs-3",
      factor_type: "EXPERIENCE",
      raw_score: 90.0,
      configured_weight: 0.20,
      normalized_weight: 0.20,
      weighted_contribution: 18.0,
      applicable: true,
      reason: "Candidate has 48 months vs required 36 months.",
    },
    {
      id: "fs-4",
      factor_type: "EDUCATION",
      raw_score: 90.0,
      configured_weight: 0.10,
      normalized_weight: 0.10,
      weighted_contribution: 9.0,
      applicable: true,
      reason: "Education requirement evaluated.",
    },
    {
      id: "fs-5",
      factor_type: "PREFERRED_SKILLS",
      raw_score: 80.0,
      configured_weight: 0.10,
      normalized_weight: 0.10,
      weighted_contribution: 8.0,
      applicable: true,
      reason: "1/1 preferred skills matched.",
    },
    {
      id: "fs-6",
      factor_type: "OTHER_REQUIREMENTS",
      raw_score: 84.0,
      configured_weight: 0.10,
      normalized_weight: 0.10,
      weighted_contribution: 8.4,
      applicable: true,
      reason: "Other non-protected requirements evaluated.",
    },
  ]);

  const [skills] = useState<ExtractedSkill[]>([
    {
      id: "sk-1",
      raw_skill_name: "retrieval augmented generation",
      canonical_skill_name: "RAG",
      years_experience: 2.0,
      confidence: 0.95,
      evidence_text: "Built retrieval augmented generation applications using pgvector",
      page_number: 1,
    },
    {
      id: "sk-2",
      raw_skill_name: "Python 3",
      canonical_skill_name: "Python",
      years_experience: 5.0,
      confidence: 0.98,
      evidence_text: "5+ years experience building Python microservices with FastAPI",
      page_number: 1,
    },
  ]);

  const [requirementMatches] = useState<RequirementMatchUI[]>([
    {
      id: "rm-1",
      requirement_type: "SKILL",
      canonical_required_value: "Python",
      requirement_level: "REQUIRED",
      hard_constraint: true,
      match_status: "MATCHED",
      candidate_value: "Python",
      confidence: 0.95,
      reason: "Canonical skill match: 'Python' matches required 'Python'.",
      evidence_text: "5+ years experience building Python microservices with FastAPI",
    },
    {
      id: "rm-2",
      requirement_type: "EXPERIENCE",
      canonical_required_value: "36 Months Experience",
      requirement_level: "REQUIRED",
      hard_constraint: true,
      match_status: "MATCHED",
      candidate_value: "48 months",
      confidence: 0.90,
      reason: "Candidate has 48 months experience, satisfying >= 36 months requirement.",
    },
    {
      id: "rm-3",
      requirement_type: "SKILL",
      canonical_required_value: "RAG",
      requirement_level: "PREFERRED",
      hard_constraint: false,
      match_status: "MATCHED",
      candidate_value: "RAG",
      confidence: 0.94,
      reason: "Canonical skill match: 'RAG' matches required 'RAG'.",
      evidence_text: "Built retrieval augmented generation applications using pgvector",
    },
    {
      id: "rm-4",
      requirement_type: "WORK_MODE",
      canonical_required_value: "HYBRID",
      requirement_level: "REQUIRED",
      hard_constraint: true,
      match_status: "UNKNOWN",
      confidence: 0.50,
      reason: "Candidate work mode preference unknown (absence of evidence).",
    },
  ]);

  const [semanticMatches] = useState<SemanticMatchUI[]>([
    {
      id: "sm-1",
      query_context: "REQUIRED_SKILLS",
      candidate_context: "SKILL_CONTEXT",
      similarity_score: 0.92,
    },
    {
      id: "sm-2",
      query_context: "RESPONSIBILITIES",
      candidate_context: "EXPERIENCE_CONTEXT",
      similarity_score: 0.88,
    },
    {
      id: "sm-3",
      query_context: "JOB_INTENT",
      candidate_context: "SUMMARY",
      similarity_score: 0.86,
    },
  ]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}/applications`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Candidate Applications Pipeline
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Deterministic AI Candidate Score & Feature Evidence</h1>
            <p className="text-slate-400 text-xs">
              Review explainable deterministic candidate match scores, hard requirement gate results, factor breakdown, and traceable resume evidence.
            </p>
          </div>
        </div>

        {/* Master Score Summary Card (Phase 9B) */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Overall Candidate Score</div>
              <div className="text-4xl font-extrabold text-blue-400 mt-1">
                {scoreData.overall_score} <span className="text-xl text-slate-500 font-normal">/ 100</span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">Hard Requirement Gate</div>
                <div className="mt-1">
                  {scoreData.eligibility_status === "PASS" ? (
                    <span className="px-3 py-1 rounded text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      ✓ PASS
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                      × FAIL
                    </span>
                  )}
                </div>
              </div>

              <div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider">Score Confidence</div>
                <div className="mt-1">
                  <span className="px-3 py-1 rounded text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                    {scoreData.confidence_tier} ({(scoreData.score_confidence * 100).toFixed(0)}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Factor Score Breakdown Table */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Factor Score Breakdown</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {factorScores.map((fs) => (
                <div key={fs.id} className="bg-slate-950 border border-slate-800 rounded-lg p-3 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">{fs.factor_type.replace("_", " ")}</span>
                    <span className="text-xs font-bold text-blue-300">
                      {fs.weighted_contribution.toFixed(1)} <span className="text-[10px] text-slate-500">pts (raw: {fs.raw_score}%)</span>
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-blue-500 h-full rounded-full"
                      style={{ width: `${Math.min(100, fs.raw_score)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-slate-400 flex items-center justify-between">
                    <span>Configured Weight: {(fs.configured_weight * 100).toFixed(0)}%</span>
                    <span>Applicable Weight: {(fs.normalized_weight * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Feature Matching & Requirement Results */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider text-purple-400">Requirement Feature Match Evaluations</h2>
            <span className="px-2.5 py-1 rounded text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20">
              Phase 9A Feature Matching Engine
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {requirementMatches.map((rm) => (
              <div key={rm.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{rm.canonical_required_value}</span>
                  <div className="flex items-center gap-1.5">
                    {rm.match_status === "MATCHED" && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ✓ MATCHED
                      </span>
                    )}
                    {rm.match_status === "UNKNOWN" && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        ? UNKNOWN
                      </span>
                    )}
                    {rm.match_status === "NOT_MATCHED" && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        × NOT MATCHED
                      </span>
                    )}
                    {rm.match_status === "PROTECTED_EXCLUDED" && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        PROTECTED EXCLUDED
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-xs text-slate-400">{rm.reason}</div>
                {rm.evidence_text && (
                  <blockquote className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded italic border-l-2 border-purple-500">
                    &ldquo;{rm.evidence_text}&rdquo;
                  </blockquote>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Semantic Vector Context Matches */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">pgvector Semantic Context Similarities</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {semanticMatches.map((sm) => (
              <div key={sm.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
                <div className="text-xs text-slate-400">
                  {sm.query_context} &bull; {sm.candidate_context}
                </div>
                <div className="text-xl font-bold text-purple-300">
                  {(sm.similarity_score * 100).toFixed(1)}% Similarity
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Extracted Skills with Evidence */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">Extracted Skills & Evidence Quotes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {skills.map((s) => (
              <div key={s.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm">{s.canonical_skill_name}</span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                      (raw: {s.raw_skill_name})
                    </span>
                  </div>
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {(s.confidence * 100).toFixed(0)}% Confidence
                  </span>
                </div>
                <blockquote className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded italic border-l-2 border-blue-500">
                  &ldquo;{s.evidence_text}&rdquo;
                </blockquote>
                <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1">
                  <span>📄 Page {s.page_number}</span>
                  <span>⏱️ {s.years_experience} Years Experience</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
