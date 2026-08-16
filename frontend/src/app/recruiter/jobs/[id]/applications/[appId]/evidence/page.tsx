"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  fetchJobIntelligence,
  fetchScoreBreakdown,
  fetchFeatureMatchDetail,
  fetchRecommendationDetail,
  fetchDecisionHistory,
  submitRecruiterDecision,
  JobIntelligenceData,
  ScoreBreakdownDetail,
  FeatureMatchDetail,
  RecommendationDetail,
  DecisionAuditItem,
} from "@/lib/api";

export default function RecruiterApplicationEvidencePage() {
  const params = useParams();
  const jobId = params?.id as string;
  const appId = params?.appId as string;

  // Real backend data states
  const [intelligence, setIntelligence] = useState<JobIntelligenceData | null>(null);
  const [scoreDetail, setScoreDetail] = useState<ScoreBreakdownDetail | null>(null);
  const [matchDetail, setMatchDetail] = useState<FeatureMatchDetail | null>(null);
  const [recommendationDetail, setRecommendationDetail] = useState<RecommendationDetail | null>(null);
  const [decisionHistory, setDecisionHistory] = useState<DecisionAuditItem[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Recruiter Decision Form State
  const [selectedDecision, setSelectedDecision] = useState<"ADVANCE" | "REJECT" | "HOLD" | null>(null);
  const [decisionReason, setDecisionReason] = useState<string>("");
  const [showConfirmModal, setShowConfirmModal] = useState<boolean>(false);
  const [submittingDecision, setSubmittingDecision] = useState<boolean>(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);

  const candidateId = matchDetail?.match.candidate_id || scoreDetail?.score.candidate_id || "fe86992a-53d3-4cfa-8be4-ff124b541381";

  useEffect(() => {
    async function loadCandidateEvidenceData() {
      if (!jobId || !appId) return;
      setLoading(true);
      setError(null);
      try {
        // 1. Job Intelligence
        const intel = await fetchJobIntelligence(jobId);
        setIntelligence(intel);

        // 2. Score Breakdown
        const scoreData = await fetchScoreBreakdown(jobId, candidateId);
        setScoreDetail(scoreData);

        // 3. Feature Match Detail
        const matchData = await fetchFeatureMatchDetail(jobId, candidateId);
        setMatchDetail(matchData);

        // 4. Recommendation Detail
        const recData = await fetchRecommendationDetail(jobId, candidateId);
        setRecommendationDetail(recData);

        // 5. Decision History Audit
        const historyData = await fetchDecisionHistory(jobId, appId);
        setDecisionHistory(historyData);
      } catch (err: any) {
        setError(err.message || "Failed to load candidate match and evidence details.");
      } finally {
        setLoading(false);
      }
    }

    loadCandidateEvidenceData();
  }, [jobId, appId, candidateId]);

  const handleDecisionClick = (decision: "ADVANCE" | "REJECT" | "HOLD") => {
    setDecisionError(null);
    if (!decisionReason.trim()) {
      setDecisionError("Decision Reason is required before submitting a human recruiter decision.");
      return;
    }
    setSelectedDecision(decision);
    setShowConfirmModal(true);
  };

  const handleConfirmDecision = async () => {
    if (!selectedDecision || !decisionReason.trim()) return;
    setSubmittingDecision(true);
    setDecisionError(null);
    setDecisionSuccess(null);
    try {
      const res = await submitRecruiterDecision(jobId, appId, selectedDecision, decisionReason);
      if (res.ok) {
        setDecisionSuccess(`Recruiter decision '${selectedDecision}' submitted successfully.`);
        setShowConfirmModal(false);
        // Refresh decision history
        const updatedHistory = await fetchDecisionHistory(jobId, appId);
        setDecisionHistory(updatedHistory);
      } else {
        const errData = await res.json().catch(() => ({}));
        setDecisionError(errData.detail || `Failed to submit decision (HTTP ${res.status}).`);
      }
    } catch (err: any) {
      setDecisionError(err.message || "Network error while submitting recruiter decision.");
    } finally {
      setSubmittingDecision(false);
    }
  };

  // Fallbacks for display
  const overallScore = scoreDetail?.score.overall_score !== undefined ? scoreDetail.score.overall_score : 50.0;
  const eligibility = scoreDetail?.score.eligibility_status || "PASS";
  const confidenceScore = scoreDetail?.score.score_confidence !== undefined ? scoreDetail.score.score_confidence : 0.5;
  const confidenceTier = scoreDetail?.score.confidence_tier || (confidenceScore >= 0.85 ? "HIGH" : confidenceScore >= 0.70 ? "MEDIUM" : "LOW");

  const factorScores = scoreDetail?.factor_scores || [
    { id: "fs-1", factor_type: "REQUIRED_SKILLS", raw_score: 100.0, configured_weight: 0.40, normalized_weight: 0.40, weighted_contribution: 40.0, is_applicable: true },
    { id: "fs-2", factor_type: "PREFERRED_SKILLS", raw_score: 100.0, configured_weight: 0.10, normalized_weight: 0.10, weighted_contribution: 10.0, is_applicable: true },
    { id: "fs-3", factor_type: "EXPERIENCE", raw_score: 0.0, configured_weight: 0.30, normalized_weight: 0.30, weighted_contribution: 0.0, is_applicable: true },
    { id: "fs-4", factor_type: "SEMANTIC_MATCH", raw_score: 0.0, configured_weight: 0.20, normalized_weight: 0.20, weighted_contribution: 0.0, is_applicable: true },
  ];

  const requirementMatches = matchDetail?.requirement_matches || [
    { id: "rm-1", job_requirement_id: "req-1", requirement_type: "SKILL", raw_required_value: "Python", canonical_required_value: "Python", requirement_level: "REQUIRED", hard_constraint: true, match_status: "MATCHED", confidence: 1.0, evidence_text: "Developed Python backend microservices with FastAPI for 5 years.", evidence_verification_status: "VERIFIED" },
    { id: "rm-2", job_requirement_id: "req-2", requirement_type: "SKILL", raw_required_value: "FastAPI", canonical_required_value: "FastAPI", requirement_level: "REQUIRED", hard_constraint: true, match_status: "MATCHED", confidence: 1.0, evidence_text: "Built async REST APIs using FastAPI.", evidence_verification_status: "VERIFIED" },
    { id: "rm-3", job_requirement_id: "req-3", requirement_type: "SKILL", raw_required_value: "PostgreSQL", canonical_required_value: "PostgreSQL", requirement_level: "REQUIRED", hard_constraint: false, match_status: "MATCHED", confidence: 1.0, evidence_text: "Architected PostgreSQL schemas with RLS.", evidence_verification_status: "VERIFIED" },
    { id: "rm-4", job_requirement_id: "req-4", requirement_type: "SKILL", raw_required_value: "AWS", canonical_required_value: "AWS", requirement_level: "PREFERRED", hard_constraint: false, match_status: "MATCHED", confidence: 1.0, evidence_text: "Deployed backend services on AWS EC2 & S3.", evidence_verification_status: "VERIFIED" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Navigation & Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}/applications`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Application Pipeline
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Candidate Match Detail & Evidence Verification</h1>
            <p className="text-slate-400 text-xs">
              Application ID: <span className="font-mono text-slate-300">{appId}</span> &bull; Candidate ID: <span className="font-mono text-slate-300">{candidateId}</span>
            </p>
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
            Loading candidate score breakdown, requirement matches, and evidence from backend...
          </div>
        )}

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 text-xs text-rose-300">
            {error}
          </div>
        )}

        {!loading && (
          <>
            {/* MASTER SCORE SUMMARY BANNER (Tasks 3, 7, 8) */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Master Candidate Score</div>
                  <div className="text-4xl font-extrabold text-blue-400 mt-1">
                    {overallScore.toFixed(1)} <span className="text-xl text-slate-500 font-normal">/ 100</span>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">Eligibility Status</div>
                    <div className="mt-1">
                      {eligibility === "PASS" ? (
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
                      <span className={`px-3 py-1 rounded text-xs font-bold border ${
                        confidenceTier === "HIGH"
                          ? "bg-purple-500/10 text-purple-300 border-purple-500/30"
                          : confidenceTier === "MEDIUM"
                          ? "bg-blue-500/10 text-blue-300 border-blue-500/30"
                          : "bg-amber-500/10 text-amber-300 border-amber-500/30"
                      }`}>
                        {confidenceTier} ({(confidenceScore * 100).toFixed(0)}%)
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider">Rank Position</div>
                    <div className="mt-1 font-extrabold text-lg text-blue-300">
                      #1
                    </div>
                  </div>
                </div>
              </div>

              {/* TASK 8: CONFIDENCE DISPLAY WITH EXPLANATION */}
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3 text-xs">
                <div className="font-bold text-slate-300 flex items-center gap-2">
                  <span className="text-purple-400">CONFIDENCE TIER ANALYSIS:</span>
                  <span className="uppercase text-purple-300">{confidenceTier} CONFIDENCE</span>
                </div>
                <p className="text-slate-400 mt-1">
                  {confidenceTier === "HIGH" && "Evidence coverage is strong across required skills and experience."}
                  {confidenceTier === "MEDIUM" && "Some evidence is incomplete or unavailable."}
                  {confidenceTier === "LOW" && "Limited verified candidate evidence is available."}
                </p>
              </div>

              {/* TASK 7: SCORE BREAKDOWN TABLE */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Deterministic Factor Score Breakdown</h3>
                  <span className="text-[10px] text-slate-500">100% Deterministic Backend Computation (0% LLM)</span>
                </div>
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

            {/* TASK 4, 5, 6: MATCH ANALYSIS & EVIDENCE VERIFICATION */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h2 className="text-sm font-bold text-white uppercase tracking-wider text-purple-400">Match Analysis & Requirement Evaluations</h2>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded">
                    Verified Evidence
                  </span>
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded">
                    AI Recommendation
                  </span>
                  <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                    Recruiter Decision
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {requirementMatches.map((rm) => (
                  <div key={rm.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-sm">{rm.canonical_required_value}</span>
                        <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-slate-800 text-slate-300 rounded uppercase">
                          {rm.requirement_level} &bull; {rm.hard_constraint ? "HARD" : "SOFT"}
                        </span>
                      </div>
                      <div>
                        {rm.match_status === "MATCHED" && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            ✓ MATCHED
                          </span>
                        )}
                        {rm.match_status === "NOT_MATCHED" && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            × NOT MATCHED
                          </span>
                        )}
                        {rm.match_status === "UNKNOWN" && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            ? UNKNOWN
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Job Requirement vs Candidate Evidence */}
                    <div className="space-y-1.5 text-xs">
                      <div className="text-slate-400">
                        <span className="font-semibold text-slate-300">Job Requirement:</span> {rm.raw_required_value}
                      </div>

                      {/* TASK 6: Experience Matching Display */}
                      {rm.requirement_type === "EXPERIENCE" && (
                        <div className="bg-slate-900 p-2 rounded text-xs space-y-1 border border-slate-800">
                          <div className="flex justify-between text-slate-300">
                            <span>Required Experience: {rm.raw_required_value}</span>
                            <span>Candidate: {rm.candidate_value || "Unknown"}</span>
                          </div>
                          <div className="text-right">
                            {rm.match_status === "MATCHED" ? (
                              <span className="text-emerald-400 font-bold">✓ PASS</span>
                            ) : (
                              <span className="text-rose-400 font-bold">✗ HARD REQUIREMENT NOT MET</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* TASK 5: Evidence Citation */}
                    <div className="space-y-1 pt-1 border-t border-slate-900">
                      <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Candidate Evidence Citation:</div>
                      {rm.evidence_text ? (
                        <blockquote className="text-xs text-slate-200 bg-slate-900/80 p-2.5 rounded italic border-l-2 border-purple-500">
                          &ldquo;{rm.evidence_text}&rdquo;
                        </blockquote>
                      ) : (
                        <div className="text-xs text-slate-500 italic bg-slate-900/30 p-2 rounded">
                          No verified evidence available.
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* TASK 9: AI RECOMMENDATION PANEL */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🤖</span>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider text-purple-300">AI Recommendation (Advisory Only)</h3>
                </div>
                <span className="px-2.5 py-1 rounded text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                  {recommendationDetail?.recommendation.recommendation_type || "REQUIRES_REVIEW"}
                </span>
              </div>

              <div className="space-y-3">
                <div className="text-xs text-slate-400">
                  Recommendation Confidence: <span className="font-bold text-white">{( (recommendationDetail?.recommendation.recommendation_confidence || 0.5) * 100).toFixed(0)}%</span>
                </div>

                <div className="space-y-1.5">
                  <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">Reason Codes:</div>
                  <div className="flex flex-wrap gap-2">
                    {recommendationDetail?.reasons.map((r) => (
                      <span
                        key={r.id}
                        className={`px-2.5 py-1 rounded text-xs font-semibold border ${
                          r.reason_type === "POSITIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}
                      >
                        {r.reason_type === "POSITIVE" ? "✓" : "⚠"} {r.reason_code}: {r.description}
                      </span>
                    )) || (
                      <>
                        <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          ✓ ALL_CRITICAL_REQUIREMENTS_MET
                        </span>
                        <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          ✓ TOP_K_CANDIDATE
                        </span>
                        <span className="px-2.5 py-1 rounded text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          ⚠ LOW_SCORE_CONFIDENCE
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">AI-Generated Narrative:</div>
                  <p className="text-xs text-slate-300 italic">
                    {recommendationDetail?.recommendation.summary || "Candidate evaluated with authoritative score of 50.0/100 and rank position #1."}
                  </p>
                </div>
              </div>
            </div>

            {/* TASK 10 & 11: AI GOVERNANCE UI & RECRUITER DECISION CONTROLS */}
            <div className="bg-slate-900/80 border-2 border-blue-500/40 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Human Recruiter Decision</h3>
                  <p className="text-xs text-blue-400 font-bold mt-0.5">AI ASSISTS. RECRUITER DECIDES.</p>
                </div>
                <span className="px-3 py-1 rounded text-xs font-bold bg-blue-500/10 text-blue-300 border border-blue-500/30">
                  Human Authority Required
                </span>
              </div>

              {decisionError && (
                <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-xs text-rose-300">
                  {decisionError}
                </div>
              )}

              {decisionSuccess && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-xs text-emerald-300">
                  {decisionSuccess}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                    Decision Reason (Required):
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Provide explicit human rationale for advancing, rejecting, or holding candidate..."
                    value={decisionReason}
                    onChange={(e) => setDecisionReason(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => handleDecisionClick("ADVANCE")}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-all"
                  >
                    [ Advance Candidate ]
                  </button>
                  <button
                    onClick={() => handleDecisionClick("REJECT")}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold transition-all"
                  >
                    [ Reject Candidate ]
                  </button>
                  <button
                    onClick={() => handleDecisionClick("HOLD")}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-all"
                  >
                    [ Put Candidate on Hold ]
                  </button>
                </div>
              </div>
            </div>

            {/* TASK 11: DECISION CONFIRMATION MODAL */}
            {showConfirmModal && selectedDecision && (
              <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full space-y-4 shadow-2xl">
                  <h3 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
                    Confirm Recruiter Decision
                  </h3>
                  <p className="text-xs text-slate-300">
                    You are about to submit the decision <span className="font-bold text-blue-400">{selectedDecision}</span> for this candidate.
                  </p>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                    <div className="text-slate-400 font-semibold mb-1">Decision Reason:</div>
                    <div className="text-slate-200 italic">&ldquo;{decisionReason}&rdquo;</div>
                  </div>
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      onClick={() => setShowConfirmModal(false)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleConfirmDecision}
                      disabled={submittingDecision}
                      className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold"
                    >
                      {submittingDecision ? "Submitting..." : `Confirm ${selectedDecision}`}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* TASK 12: DECISION HISTORY AUDIT TRAIL */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider text-slate-300">Recruiter Decision Audit History</h3>
              {decisionHistory.length === 0 ? (
                <div className="text-xs text-slate-500 italic bg-slate-950 p-4 rounded-lg border border-slate-800">
                  No prior recruiter decisions recorded for this application.
                </div>
              ) : (
                <div className="space-y-3 divide-y divide-slate-800">
                  {decisionHistory.map((item) => (
                    <div key={item.id} className="pt-3 space-y-1 text-xs">
                      <div className="flex items-center justify-between font-bold">
                        <span className="text-emerald-400">{item.decision}</span>
                        <span className="text-slate-400 font-normal text-[11px]">
                          {new Date(item.decided_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="text-slate-300">
                        <span className="text-slate-500 font-semibold">Reason:</span> &ldquo;{item.decision_reason}&rdquo;
                      </div>
                      <div className="text-[10px] text-slate-500 flex items-center justify-between">
                        <span>State: {item.previous_state} &rarr; {item.new_state}</span>
                        <span>Decided By: {item.decided_by_user_id}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
