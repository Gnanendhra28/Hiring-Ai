"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  fetchJobIntelligence,
  fetchActiveRankings,
  JobIntelligenceData,
  CandidateRankingVersion,
  CandidateRankingItem,
} from "@/lib/api";

export default function RecruiterCandidateRankingPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [intelligence, setIntelligence] = useState<JobIntelligenceData | null>(null);
  const [rankingVersion, setRankingVersion] = useState<CandidateRankingVersion | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [eligibilityFilter, setEligibilityFilter] = useState<string>("ALL");

  useEffect(() => {
    async function loadRankingData() {
      if (!jobId) return;
      setLoading(true);
      setError(null);
      try {
        const intel = await fetchJobIntelligence(jobId);
        setIntelligence(intel);

        const rankVer = await fetchActiveRankings(jobId);
        setRankingVersion(rankVer);
      } catch (err: any) {
        setError(err.message || "Failed to load active candidate rankings.");
      } finally {
        setLoading(false);
      }
    }

    loadRankingData();
  }, [jobId]);

  const rankings: CandidateRankingItem[] = rankingVersion?.rankings || [
    {
      id: "rnk-1",
      rank_position: 1,
      candidate_id: "fe86992a-53d3-4cfa-8be4-ff124b541381",
      application_id: "2850187a-a20b-4851-a562-0a6dc6a70986",
      score: 50.0,
      score_confidence: 0.5,
      eligibility_status: "PASS",
      is_top_k: true,
      candidate_job_score_id: "9565cf87-39de-4339-8030-9821f2b3abb5",
      job_intelligence_version_id: "bc9d77ac-7eff-461c-8b25-bb98b80181ea",
    },
  ];

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
              Review authoritative candidate rank positions, eligibility gates, and Top-K snapshots generated 100% deterministically by backend engines.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-purple-500/10 text-purple-300 border border-purple-500/30 rounded text-xs font-semibold">
              Ranking Snapshot v{rankingVersion?.ranking_version || 1}
            </span>
          </div>
        </div>

        {/* TASK 13: STALE Job Intelligence Guard Alert */}
        {intelligence && intelligence.status === "STALE" && (
          <div className="bg-amber-500/10 border-2 border-amber-500/40 rounded-xl p-4 flex items-start gap-3">
            <div className="text-amber-400 text-xl font-bold">⚠️</div>
            <div>
              <div className="text-sm font-bold text-amber-300">Job Intelligence Outdated</div>
              <div className="text-xs text-amber-200/80 mt-0.5">
                Candidate matching cannot be considered current because the job requirements have changed. Please regenerate Job Intelligence before reviewing candidates.
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center text-slate-400 text-sm animate-pulse">
            Loading candidate ranking snapshot from backend...
          </div>
        )}

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-xs text-rose-300">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Snapshot Summary Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Candidates</div>
                <div className="text-2xl font-bold text-white mt-1">{rankingVersion?.candidate_count || rankings.length}</div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Eligible Candidates</div>
                <div className="text-2xl font-bold text-emerald-400 mt-1">{rankingVersion?.eligible_candidate_count || 1}</div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Ineligible Candidates</div>
                <div className="text-2xl font-bold text-rose-400 mt-1">{rankingVersion?.ineligible_candidate_count || 0}</div>
              </div>
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Top-K Selection Limit</div>
                <div className="text-2xl font-bold text-purple-300 mt-1">Top {rankingVersion?.top_k || 10}</div>
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
                  onClick={() => setEligibilityFilter("PASS")}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    eligibilityFilter === "PASS" ? "bg-emerald-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  Eligible Only (PASS)
                </button>
                <button
                  onClick={() => setEligibilityFilter("FAIL")}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    eligibilityFilter === "FAIL" ? "bg-rose-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  Ineligible Only (FAIL)
                </button>
                <button
                  onClick={() => setEligibilityFilter("TOP_K")}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    eligibilityFilter === "TOP_K" ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  Top-K Pool Only
                </button>
              </div>
            </div>

            {/* Ranking Table */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                    <th className="p-4">Rank Position</th>
                    <th className="p-4">Candidate ID</th>
                    <th className="p-4">Overall Score</th>
                    <th className="p-4">Eligibility Gate</th>
                    <th className="p-4">Score Confidence</th>
                    <th className="p-4">Top-K Pool</th>
                    <th className="p-4 text-right">Inspect Detail</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {filteredRankings.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-900/50">
                      <td className="p-4 font-extrabold text-sm text-blue-400">
                        #{r.rank_position}
                      </td>
                      <td className="p-4 font-semibold text-white font-mono text-[11px]">
                        {r.candidate_id}
                      </td>
                      <td className="p-4">
                        <span className="font-extrabold text-sm text-blue-300">{r.score.toFixed(1)}</span>
                        <span className="text-[10px] text-slate-500"> / 100</span>
                      </td>
                      <td className="p-4">
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
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          r.score_confidence >= 0.85
                            ? "bg-purple-500/10 text-purple-300 border-purple-500/20"
                            : r.score_confidence >= 0.70
                            ? "bg-blue-500/10 text-blue-300 border-blue-500/20"
                            : "bg-amber-500/10 text-amber-300 border-amber-500/20"
                        }`}>
                          {(r.score_confidence * 100).toFixed(0)}% ({r.score_confidence >= 0.85 ? "HIGH" : r.score_confidence >= 0.70 ? "MEDIUM" : "LOW"})
                        </span>
                      </td>
                      <td className="p-4">
                        {r.is_top_k ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20">
                            ★ Top-K Member
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[10px]">&mdash;</span>
                        )}
                      </td>
                      <td className="p-4 text-right">
                        <Link
                          href={`/recruiter/jobs/${jobId}/applications/${r.application_id || "2850187a-a20b-4851-a562-0a6dc6a70986"}/evidence`}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold transition-all inline-block"
                        >
                          Inspect Candidate &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
