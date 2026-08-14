"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface CandidateRankingUI {
  id: string;
  rank_position: number;
  candidate_name: string;
  candidate_id: string;
  application_id: string;
  score: number;
  score_confidence: number;
  confidence_tier: "HIGH" | "MEDIUM" | "LOW";
  eligibility_status: "PASS" | "FAIL" | "UNKNOWN";
  is_top_k: boolean;
  hard_req_summary: string;
}

export default function RecruiterCandidateRankingPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [topKFilter, setTopKFilter] = useState<number>(10);
  const [eligibilityFilter, setEligibilityFilter] = useState<string>("ALL");

  const [rankingVersion] = useState({
    ranking_version: 1,
    top_k: 10,
    candidate_count: 4,
    eligible_candidate_count: 3,
    ineligible_candidate_count: 1,
    created_at: "2026-08-14T17:00:00Z",
  });

  const [rankings] = useState<CandidateRankingUI[]>([
    {
      id: "rnk-1",
      rank_position: 1,
      candidate_name: "Candidate A (Alex Chen)",
      candidate_id: "cand-1",
      application_id: "app-1",
      score: 94.5,
      score_confidence: 0.96,
      confidence_tier: "HIGH",
      eligibility_status: "PASS",
      is_top_k: true,
      hard_req_summary: "✓ Python >= 36m, ✓ Work Mode",
    },
    {
      id: "rnk-2",
      rank_position: 2,
      candidate_name: "Candidate B (Sarah Jenkins)",
      candidate_id: "cand-2",
      application_id: "app-2",
      score: 91.2,
      score_confidence: 0.92,
      confidence_tier: "HIGH",
      eligibility_status: "PASS",
      is_top_k: true,
      hard_req_summary: "✓ Python >= 36m, ✓ Work Mode",
    },
    {
      id: "rnk-3",
      rank_position: 3,
      candidate_name: "Candidate C (Marcus Vance)",
      candidate_id: "cand-3",
      application_id: "app-3",
      score: 87.6,
      score_confidence: 0.88,
      confidence_tier: "MEDIUM",
      eligibility_status: "PASS",
      is_top_k: true,
      hard_req_summary: "✓ Python >= 36m, ✓ Work Mode",
    },
    {
      id: "rnk-4",
      rank_position: 4,
      candidate_name: "Candidate D (Dmitri Volkov)",
      candidate_id: "cand-4",
      application_id: "app-4",
      score: 98.2,
      score_confidence: 0.95,
      confidence_tier: "HIGH",
      eligibility_status: "FAIL",
      is_top_k: false,
      hard_req_summary: "× Failed Hard Req: Kubernetes >= 24m",
    },
  ]);

  const filteredRankings = rankings.filter((r) => {
    if (eligibilityFilter === "PASS" && r.eligibility_status !== "PASS") return false;
    if (eligibilityFilter === "FAIL" && r.eligibility_status !== "FAIL") return false;
    if (eligibilityFilter === "TOP_K" && !r.is_top_k) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Job Requisition Workspace
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Deterministic AI Candidate Ranking & Top-K Selection</h1>
            <p className="text-slate-400 text-xs">
              Review authoritative candidate rank positions, eligibility gates, and Top-K snapshots generated 100% deterministically from Phase 9B scores.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-purple-500/10 text-purple-300 border border-purple-500/30 rounded text-xs font-semibold">
              Ranking Snapshot v{rankingVersion.ranking_version}
            </span>
          </div>
        </div>

        {/* Snapshot Summary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Candidates</div>
            <div className="text-2xl font-bold text-white mt-1">{rankingVersion.candidate_count}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Eligible Candidates</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{rankingVersion.eligible_candidate_count}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Ineligible Candidates</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">{rankingVersion.ineligible_candidate_count}</div>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Top-K Selection Limit</div>
            <div className="text-2xl font-bold text-purple-300 mt-1">Top {rankingVersion.top_k}</div>
          </div>
        </div>

        {/* Display Filter Bar */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold uppercase">Filter View:</span>
            <button
              onClick={() => setEligibilityFilter("ALL")}
              className={`px-3 py-1 rounded text-xs font-semibold ${
                eligibilityFilter === "ALL" ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              All Candidates
            </button>
            <button
              onClick={() => setEligibilityFilter("TOP_K")}
              className={`px-3 py-1 rounded text-xs font-semibold ${
                eligibilityFilter === "TOP_K" ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Top-K Only
            </button>
            <button
              onClick={() => setEligibilityFilter("PASS")}
              className={`px-3 py-1 rounded text-xs font-semibold ${
                eligibilityFilter === "PASS" ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Eligible (PASS)
            </button>
            <button
              onClick={() => setEligibilityFilter("FAIL")}
              className={`px-3 py-1 rounded text-xs font-semibold ${
                eligibilityFilter === "FAIL" ? "bg-rose-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              Ineligible (FAIL)
            </button>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold uppercase">Top-K Display Limit:</span>
            {[5, 10, 20, 50].map((k) => (
              <button
                key={k}
                onClick={() => setTopKFilter(k)}
                className={`px-2.5 py-1 rounded text-xs font-mono font-semibold ${
                  topKFilter === k ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                K={k}
              </button>
            ))}
          </div>
        </div>

        {/* Candidate Ranking Table */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Rank</th>
                <th className="py-3 px-4">Candidate</th>
                <th className="py-3 px-4">Phase 9B Score</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Eligibility</th>
                <th className="py-3 px-4">Top-K Slot</th>
                <th className="py-3 px-4">Hard Requirements</th>
                <th className="py-3 px-4 text-right">Evidence Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredRankings.map((r) => (
                <tr key={r.id} className="hover:bg-slate-900/70 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-white text-sm">
                    #{r.rank_position}
                  </td>
                  <td className="py-3.5 px-4 font-bold text-white">
                    {r.candidate_name}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-extrabold text-blue-400 text-sm">{r.score}</span>
                    <span className="text-slate-500 font-normal"> / 100</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      {r.confidence_tier} ({(r.score_confidence * 100).toFixed(0)}%)
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    {r.eligibility_status === "PASS" ? (
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ✓ PASS
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        × FAIL
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    {r.is_top_k ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        ✓ Top {rankingVersion.top_k}
                      </span>
                    ) : (
                      <span className="text-slate-600 text-xs">—</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-400">
                    {r.hard_req_summary}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      href={`/recruiter/jobs/${jobId}/applications/${r.application_id}/evidence`}
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-blue-300 rounded font-semibold text-xs transition-colors inline-block"
                    >
                      View Evidence & Score Breakdown &rarr;
                    </Link>
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
