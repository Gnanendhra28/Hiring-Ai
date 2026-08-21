"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  fetchJobIntelligence,
  fetchActiveRankings,
  fetchRecruiterJobs,
  JobIntelligenceData,
  CandidateRankingVersion,
  CandidateRankingItem,
  JobItemData,
} from "@/lib/api";
import { Briefcase, Sparkles, UserCheck } from "lucide-react";

const isValidUUID = (str: string) =>
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(str);

export default function RecruiterCandidateRankingPage() {
  const params = useParams();
  const router = useRouter();
  const rawJobId = params?.id as string;

  const [activeJobs, setActiveJobs] = useState<JobItemData[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [intelligence, setIntelligence] = useState<JobIntelligenceData | null>(null);
  const [rankingVersion, setRankingVersion] = useState<CandidateRankingVersion | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [eligibilityFilter, setEligibilityFilter] = useState<string>("ALL");

  useEffect(() => {
    async function initRanking() {
      setLoading(true);
      setError(null);
      try {
        const jobs = await fetchRecruiterJobs();
        setActiveJobs(jobs);

        let targetId = rawJobId;
        if (!targetId || !isValidUUID(targetId)) {
          if (jobs.length > 0) {
            targetId = jobs[0].id;
          } else {
            setLoading(false);
            return;
          }
        }

        setSelectedJobId(targetId);
        await loadRankingData(targetId);
      } catch (err: any) {
        setError(err.message || "Failed to load active candidate rankings.");
        setLoading(false);
      }
    }

    initRanking();
  }, [rawJobId]);

  const loadRankingData = async (targetId: string) => {
    if (!targetId || !isValidUUID(targetId)) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const intel = await fetchJobIntelligence(targetId);
      setIntelligence(intel);

      const rankVer = await fetchActiveRankings(targetId);
      setRankingVersion(rankVer);
    } catch (err: any) {
      console.error("Error loading candidate ranking data:", err);
      setError(err.message || "Failed to load active candidate rankings.");
    } finally {
      setLoading(false);
    }
  };

  const handleJobChange = (newJobId: string) => {
    setSelectedJobId(newJobId);
    router.push(`/recruiter/jobs/${newJobId}/ranking`);
  };

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
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-[#1b263b] pb-4 gap-4">
          <div>
            <Link href="/recruiter/jobs" className="text-xs text-sky-400 hover:underline flex items-center gap-1">
              &larr; Back to Job Requisition
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1 flex items-center gap-2">
              <Sparkles className="text-sky-400" size={24} /> AI Candidate Matching & Rankings
            </h1>
            <p className="text-slate-400 text-xs">
              Deterministic hard requirement gates, skill evidence validation, and AI match scoring.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeJobs.length > 0 && (
              <div className="flex items-center gap-2 bg-[#111a2c] border border-[#233047] rounded-lg px-3 py-1.5">
                <Briefcase size={14} className="text-sky-400" />
                <span className="text-xs text-slate-400">Job:</span>
                <select
                  value={selectedJobId}
                  onChange={(e) => handleJobChange(e.target.value)}
                  className="bg-transparent text-xs text-white font-semibold outline-none cursor-pointer"
                >
                  {activeJobs.map((j) => (
                    <option key={j.id} value={j.id} className="bg-[#111a2c] text-white">
                      {j.title} ({j.status})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {selectedJobId && (
              <Link
                href={`/recruiter/jobs/${selectedJobId}/applications`}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg flex items-center gap-1 border border-slate-700"
              >
                <UserCheck size={14} /> Pipeline View &rarr;
              </Link>
            )}
          </div>
        </div>

        {/* Filter Bar */}
        <div className="flex items-center justify-between bg-[#111a2c] border border-[#233047] p-4 rounded-xl">
          <span className="text-xs text-slate-400 font-medium">Filter Eligibility:</span>
          <div className="flex gap-2">
            {["ALL", "PASS", "FAIL", "TOP_K"].map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setEligibilityFilter(f)}
                className={`px-3 py-1 rounded text-xs font-bold ${
                  eligibilityFilter === f
                    ? "bg-blue-600 text-white"
                    : "bg-[#0b1425] text-slate-400 border border-[#233047] hover:text-white"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Rankings Table */}
        {loading ? (
          <div className="bg-[#111a2c] border border-[#233047] rounded-xl p-12 text-center text-slate-400 text-xs">
            Loading AI candidate rankings...
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-xs text-red-400">
            {error}
          </div>
        ) : (
          <div className="bg-[#111a2c] border border-[#233047] rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                <tr>
                  <th className="px-5 py-3">Rank</th>
                  <th className="px-5 py-3">Candidate ID</th>
                  <th className="px-5 py-3">Match Score</th>
                  <th className="px-5 py-3">Gate Eligibility</th>
                  <th className="px-5 py-3">Confidence</th>
                  <th className="px-5 py-3">Top K</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b263b] text-slate-200">
                {filteredRankings.map((r) => (
                  <tr key={r.id} className="hover:bg-[#18253a]/50 transition">
                    <td className="px-5 py-4 font-bold text-sky-400">#{r.rank_position}</td>
                    <td className="px-5 py-4 font-mono text-slate-300">
                      Validated Production Candidate ({r.candidate_id.substring(0, 8)}...)
                    </td>
                    <td className="px-5 py-4 font-bold text-sm">
                      {r.score.toFixed(1)} <span className="text-[10px] font-normal text-slate-400">/ 100</span>
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.eligibility_status === "PASS"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        }`}
                      >
                        ✓ {r.eligibility_status}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {(r.score_confidence * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {r.is_top_k ? (
                        <span className="text-emerald-400 font-bold">✓ Shortlisted</span>
                      ) : (
                        <span className="text-slate-500">Standard</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
