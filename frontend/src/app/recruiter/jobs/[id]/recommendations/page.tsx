"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface CandidateRecommendationUI {
  id: string;
  candidate_id: string;
  candidate_name: string;
  application_id: string;
  rank_position: number;
  score: number;
  score_confidence: number;
  eligibility_status: "PASS" | "FAIL" | "UNKNOWN";
  is_top_k: boolean;
  recommendation_type: "STRONGLY_RECOMMEND_REVIEW" | "RECOMMEND_REVIEW" | "NEUTRAL_REVIEW" | "REQUIRES_REVIEW" | "NOT_RECOMMENDED_FOR_REVIEW";
  recommendation_confidence: number;
  summary: string;
  strengths: string[];
  gaps: string[];
  evidence_quote: string;
  review_state: string;
  recruiter_decision: "ADVANCE" | "REJECT" | "HOLD" | "REQUEST_MORE_INFORMATION" | "NO_DECISION";
}

export default function RecruiterCandidateRecommendationsPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [recommendations, setRecommendations] = useState<CandidateRecommendationUI[]>([
    {
      id: "rec-1",
      candidate_id: "cand-1",
      candidate_name: "Candidate A (Alex Chen)",
      application_id: "app-1",
      rank_position: 1,
      score: 94.5,
      score_confidence: 0.96,
      eligibility_status: "PASS",
      is_top_k: true,
      recommendation_type: "STRONGLY_RECOMMEND_REVIEW",
      recommendation_confidence: 0.94,
      summary: "Candidate satisfies all critical required skills with strong RAG architecture alignment and 5+ years Python experience.",
      strengths: [
        "5+ years Python microservices experience",
        "Demonstrated RAG & pgvector implementation",
        "Satisfies all critical hard requirements",
      ],
      gaps: ["Preferred Azure cloud experience not explicitly demonstrated"],
      evidence_quote: "Built retrieval augmented generation applications using pgvector and FastAPI.",
      review_state: "PENDING_REVIEW",
      recruiter_decision: "NO_DECISION",
    },
    {
      id: "rec-2",
      candidate_id: "cand-2",
      candidate_name: "Candidate B (Sarah Jenkins)",
      application_id: "app-2",
      rank_position: 2,
      score: 91.2,
      score_confidence: 0.92,
      eligibility_status: "PASS",
      is_top_k: true,
      recommendation_type: "RECOMMEND_REVIEW",
      recommendation_confidence: 0.91,
      summary: "Solid technical background satisfying experience and core Python requirements.",
      strengths: [
        "4+ years Python backend development",
        "Satisfies all critical hard requirements",
      ],
      gaps: ["RAG architecture experience is basic"],
      evidence_quote: "Maintained Python REST services with FastAPI and PostgreSQL.",
      review_state: "PENDING_REVIEW",
      recruiter_decision: "NO_DECISION",
    },
  ]);

  const handleDecision = (recId: string, decision: "ADVANCE" | "REJECT" | "HOLD" | "REQUEST_MORE_INFORMATION") => {
    setRecommendations((prev) =>
      prev.map((r) =>
        r.id === recId
          ? {
              ...r,
              recruiter_decision: decision,
              review_state: "DECIDED",
            }
          : r
      )
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}/ranking`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Deterministic Candidate Ranking
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">AI Candidate Recommendation & Recruiter Decision Hub</h1>
            <p className="text-slate-400 text-xs">
              Review explainable AI recommendation summaries, evidence citations, strengths, and gaps, and execute explicit human recruiter hiring decisions.
            </p>
          </div>
          <div className="px-3 py-1 bg-purple-500/10 text-purple-300 border border-purple-500/30 rounded text-xs font-semibold">
            Governance Boundary: AI Assists &bull; Recruiter Decides
          </div>
        </div>

        {/* Candidate Recommendation Cards */}
        <div className="space-y-6">
          {recommendations.map((r) => (
            <div key={r.id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-slate-400">Rank #{r.rank_position}</span>
                    <h2 className="text-lg font-bold text-white">{r.candidate_name}</h2>
                    {r.is_top_k && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        ✓ Top 10
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Authoritative Score: <span className="text-blue-400 font-bold">{r.score} / 100</span> &bull; Confidence: {(r.score_confidence * 100).toFixed(0)}% &bull; Eligibility: <span className="text-emerald-400 font-bold">{r.eligibility_status}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {r.recommendation_type === "STRONGLY_RECOMMEND_REVIEW" && (
                    <span className="px-3 py-1 rounded text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      ★ STRONGLY RECOMMEND REVIEW
                    </span>
                  )}
                  {r.recommendation_type === "RECOMMEND_REVIEW" && (
                    <span className="px-3 py-1 rounded text-xs font-bold bg-blue-500/15 text-blue-300 border border-blue-500/30">
                      ✓ RECOMMEND REVIEW
                    </span>
                  )}

                  {r.recruiter_decision !== "NO_DECISION" ? (
                    <span className="px-3 py-1 rounded text-xs font-bold bg-purple-600 text-white font-mono">
                      DECISION: {r.recruiter_decision}
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded text-xs font-semibold bg-slate-800 text-slate-400">
                      {r.review_state}
                    </span>
                  )}
                </div>
              </div>

              {/* AI Narrative Summary */}
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-4 space-y-2">
                <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">AI Narrative Summary & Reasoning</div>
                <p className="text-xs text-slate-300 leading-relaxed">{r.summary}</p>
              </div>

              {/* Strengths & Gaps Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4 space-y-2">
                  <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Demonstrated Strengths</span>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {r.strengths.map((s, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <span className="text-emerald-400 font-bold">✓</span> {s}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4 space-y-2">
                  <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Skill & Qualification Gaps</span>
                  <ul className="space-y-1 text-xs text-slate-300">
                    {r.gaps.map((g, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <span className="text-amber-400 font-bold">⚠</span> {g}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Traceable Evidence Quote */}
              <blockquote className="text-xs text-slate-300 bg-slate-950 p-3 rounded italic border-l-2 border-purple-500">
                &ldquo;{r.evidence_quote}&rdquo;
              </blockquote>

              {/* Explicit Human Recruiter Decision Actions */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
                <div className="text-xs text-slate-400">
                  Select Recruiter Decision: <span className="text-slate-500 font-normal">(Human Authorization Required)</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDecision(r.id, "ADVANCE")}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded transition-colors"
                  >
                    Advance Candidate
                  </button>
                  <button
                    onClick={() => handleDecision(r.id, "HOLD")}
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded transition-colors"
                  >
                    Place on Hold
                  </button>
                  <button
                    onClick={() => handleDecision(r.id, "REQUEST_MORE_INFORMATION")}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded transition-colors"
                  >
                    Request Info
                  </button>
                  <button
                    onClick={() => handleDecision(r.id, "REJECT")}
                    className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded transition-colors"
                  >
                    Reject Candidate
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
