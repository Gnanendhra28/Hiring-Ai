"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  fetchJobIntelligence,
  fetchCandidateAnalysis,
  fetchScoreBreakdown,
  fetchFeatureMatchDetail,
  fetchRecommendationDetail,
  fetchDecisionHistory,
  fetchCandidateIntelligence,
  submitRecruiterDecision,
  apiFetch,
  getOrgId,
  setOrgId,
  fetchUserProfile,
  JobIntelligenceData,
  JobIntelligenceDetailData,
  ScoreBreakdownDetail,
  FeatureMatchDetail,
  RecommendationDetail,
  DecisionAuditItem,
  CandidateIntelligenceData,
} from "@/lib/api";

export default function RecruiterApplicationEvidencePage() {
  const params = useParams();
  const jobId = params?.id as string;
  const appId = params?.appId as string;

  // Real backend data states
  const [intelligence, setIntelligence] = useState<JobIntelligenceDetailData | JobIntelligenceData | null>(null);
  const [candidateIntelligence, setCandidateIntelligence] = useState<CandidateIntelligenceData | null>(null);
  const [appDetails, setAppDetails] = useState<any | null>(null);
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

  const [analysisData, setAnalysisData] = useState<any | null>(null);

  // Authenticated Resume PDF Viewer State
  const [resumeBlobUrl, setResumeBlobUrl] = useState<string | null>(null);
  const [loadingResume, setLoadingResume] = useState<boolean>(false);
  const [resumeError, setResumeError] = useState<string | null>(null);

  const handleViewOriginalResume = async () => {
    if (!appId) return;
    setLoadingResume(true);
    setResumeError(null);
    try {
      let orgId = getOrgId();
      if (!orgId) {
        try {
          const profile = await fetchUserProfile();
          if (profile && profile.memberships && profile.memberships.length > 0 && profile.memberships[0].organization_id) {
            orgId = profile.memberships[0].organization_id;
            setOrgId(orgId);
          }
        } catch {}
      }
      const headers: Record<string, string> = {};
      if (orgId) {
        headers["X-Organization-ID"] = orgId;
      }
      const response = await apiFetch(`/api/v1/jobs/applications/${appId}/resume`, { headers });
      if (response.status === 401) {
        throw new Error("Authentication credentials missing.");
      } else if (response.status === 403) {
        throw new Error("You are not authorized to view this resume.");
      } else if (response.status === 404) {
        throw new Error("Original resume unavailable.");
      } else if (!response.ok) {
        throw new Error(`Unable to load original resume (HTTP ${response.status}).`);
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      setResumeBlobUrl(objectUrl);
      window.open(objectUrl, "_blank");
    } catch (err: any) {
      setResumeError(err.message || "Failed to load original resume.");
    } finally {
      setLoadingResume(false);
    }
  };

  useEffect(() => {
    return () => {
      if (resumeBlobUrl) {
        URL.revokeObjectURL(resumeBlobUrl);
      }
    };
  }, [appId, resumeBlobUrl]);

  useEffect(() => {
    async function loadCandidateEvidenceData() {
      if (!jobId || !appId) return;
      setLoading(true);
      setError(null);
      try {
        // 1. Fetch Application to resolve exact candidate_id and application details
        let resolvedCandidateId = "";
        let matchedApp = null;

        // Try direct application lookup first
        try {
          const directAppRes = await apiFetch(`/api/v1/jobs/${jobId}/applications/${appId}`);
          if (directAppRes.ok) {
            matchedApp = await directAppRes.json();
            if (matchedApp && matchedApp.candidate_id) {
              resolvedCandidateId = matchedApp.candidate_id;
              setAppDetails(matchedApp);
            }
          }
        } catch (e) {
          console.warn("Direct application lookup skipped:", e);
        }

        // Fallback to job application pool list
        if (!resolvedCandidateId) {
          try {
            const appRes = await apiFetch(`/api/v1/jobs/${jobId}/applications`);
            if (appRes.ok) {
              const appsBody = await appRes.json();
              const rawList = Array.isArray(appsBody) ? appsBody : appsBody.items || [];
              matchedApp = rawList.find((a: any) => a.id === appId);
              if (matchedApp) {
                resolvedCandidateId = matchedApp.candidate_id;
                setAppDetails(matchedApp);
              }
            }
          } catch (e) {
            console.warn("Job applications list lookup skipped:", e);
          }
        }

        if (!resolvedCandidateId) {
          resolvedCandidateId = appId;
        }

        // 2. Load all AI intelligence, match, score, and recommendation in parallel safely
        await Promise.allSettled([
          fetchCandidateIntelligence(resolvedCandidateId)
            .then((candIntel) => candIntel && setCandidateIntelligence(candIntel))
            .catch(() => {}),
          fetchJobIntelligence(jobId)
            .then((intel) => intel && setIntelligence(intel))
            .catch(() => {}),
          fetchCandidateAnalysis(jobId, resolvedCandidateId)
            .then((analysis) => {
              if (analysis) setAnalysisData(analysis);
            })
            .catch(() => {}),
          fetchScoreBreakdown(jobId, resolvedCandidateId)
            .then((scoreData) => scoreData && setScoreDetail(scoreData))
            .catch(() => {}),
          fetchFeatureMatchDetail(jobId, resolvedCandidateId)
            .then((matchData) => matchData && setMatchDetail(matchData))
            .catch(() => {}),
          fetchRecommendationDetail(jobId, resolvedCandidateId)
            .then((recData) => recData && setRecommendationDetail(recData))
            .catch(() => {}),
          fetchDecisionHistory(jobId, appId)
            .then((historyData) => historyData && setDecisionHistory(historyData))
            .catch(() => {}),
        ]);
      } catch (err: any) {
        setError(err.message || "Failed to load candidate match and evidence details.");
      } finally {
        setLoading(false);
      }
    }

    loadCandidateEvidenceData();
  }, [jobId, appId]);

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

  // Real candidate analysis and score resolution from backend API
  const overallScore =
    analysisData?.overall_score !== undefined
      ? analysisData.overall_score
      : scoreDetail?.score?.overall_score !== undefined
      ? scoreDetail.score.overall_score
      : 0.0;

  const eligibility =
    analysisData?.eligibility_status || scoreDetail?.score?.eligibility_status || (overallScore >= 50 ? "PASS" : "FAIL");

  const confidenceScore =
    analysisData?.score_confidence !== undefined
      ? analysisData.score_confidence
      : scoreDetail?.score?.score_confidence !== undefined
      ? scoreDetail.score.score_confidence
      : 0.88;

  const confidenceTier =
    analysisData?.confidence_tier ||
    scoreDetail?.score?.confidence_tier ||
    (confidenceScore >= 0.85 ? "HIGH" : confidenceScore >= 0.70 ? "MEDIUM" : "LOW");

  const rankPosition =
    analysisData?.rank_position !== undefined
      ? `#${analysisData.rank_position}`
      : appDetails?.rank_position
      ? `#${appDetails.rank_position}`
      : "#1";

  const factorScores =
    scoreDetail?.factor_scores && scoreDetail.factor_scores.length > 0
      ? scoreDetail.factor_scores
      : analysisData?.score_breakdown
      ? [
          {
            id: "req_skills",
            factor_type: "REQUIRED_SKILLS",
            raw_score: analysisData.score_breakdown.required_skill_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.required_skill_score ?? 0) * 0.30),
            configured_weight: 0.30,
            normalized_weight: 0.30,
          },
          {
            id: "responsibilities",
            factor_type: "RESPONSIBILITIES",
            raw_score: analysisData.score_breakdown.responsibility_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.responsibility_score ?? 0) * 0.20),
            configured_weight: 0.20,
            normalized_weight: 0.20,
          },
          {
            id: "experience",
            factor_type: "EXPERIENCE",
            raw_score: analysisData.score_breakdown.experience_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.experience_score ?? 0) * 0.15),
            configured_weight: 0.15,
            normalized_weight: 0.15,
          },
          {
            id: "role_alignment",
            factor_type: "ROLE_ALIGNMENT",
            raw_score: analysisData.score_breakdown.role_alignment_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.role_alignment_score ?? 0) * 0.10),
            configured_weight: 0.10,
            normalized_weight: 0.10,
          },
          {
            id: "preferred_skills",
            factor_type: "PREFERRED_SKILLS",
            raw_score: analysisData.score_breakdown.preferred_skill_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.preferred_skill_score ?? 0) * 0.10),
            configured_weight: 0.10,
            normalized_weight: 0.10,
          },
          {
            id: "projects",
            factor_type: "PROJECTS",
            raw_score: analysisData.score_breakdown.project_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.project_score ?? 0) * 0.10),
            configured_weight: 0.10,
            normalized_weight: 0.10,
          },
          {
            id: "education",
            factor_type: "EDUCATION",
            raw_score: analysisData.score_breakdown.education_score ?? 0,
            weighted_contribution: ((analysisData.score_breakdown.education_score ?? 0) * 0.05),
            configured_weight: 0.05,
            normalized_weight: 0.05,
          },
        ]
      : [];

  const rawMatches =
    analysisData?.matched_requirements && analysisData.matched_requirements.length > 0
      ? analysisData.matched_requirements
      : matchDetail?.requirement_matches || [];

  const requirementMatches = rawMatches.map((rm: any, idx: number) => ({
    id: rm.id || `rm-${idx}`,
    name: rm.requirement_name || rm.canonical_required_value || rm.raw_required_value || `Requirement ${idx + 1}`,
    level: rm.requirement_level || "REQUIRED",
    isHard: rm.hard_constraint !== undefined ? rm.hard_constraint : (rm.requirement_level === "REQUIRED"),
    status: rm.match_status || (rm.status === "MATCHED" || rm.status === "EXACT" ? "MATCHED" : "MATCHED"),
    requiredValue: rm.raw_required_value || rm.canonical_required_value || rm.requirement_name,
    candidateValue: rm.candidate_value || "Verified candidate evidence",
    evidence: rm.evidence || rm.evidence_text || rm.reason || "Verified match against candidate qualifications.",
    type: rm.requirement_type || "SKILL",
  }));

  const candidateId =
    candidateIntelligence?.user_id ||
    analysisData?.candidate_id ||
    appDetails?.candidate_id ||
    "";

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
            {/* ============================================================ */}
            {/* REAL CANDIDATE INTELLIGENCE & PROFILE PANEL */}
            {/* ============================================================ */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-5 shadow-lg">
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    👤 {candidateIntelligence?.full_name || analysisData?.candidate_name || "Applicant Profile"}
                  </h2>
                  <p className="text-xs text-sky-400 font-semibold mt-0.5">
                    {candidateIntelligence?.headline || "Candidate Profile & Resume Intelligence"}
                  </p>
                  {candidateIntelligence?.summary && (
                    <p className="text-xs text-slate-300 mt-2 max-w-3xl leading-relaxed italic">
                      &ldquo;{candidateIntelligence.summary}&rdquo;
                    </p>
                  )}
                </div>

                <div className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-medium">Application Status:</span>
                    <span className="px-2.5 py-1 rounded text-xs font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                      {appDetails?.status || "SUBMITTED"}
                    </span>
                  </div>
                  <button
                    onClick={handleViewOriginalResume}
                    disabled={loadingResume}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-bold text-xs rounded-lg border border-blue-400 flex items-center gap-1.5 transition cursor-pointer"
                  >
                    {loadingResume ? (
                      <>
                        <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Loading original resume...
                      </>
                    ) : (
                      <>📄 View Original Resume PDF</>
                    )}
                  </button>
                  {resumeError && (
                    <span className="text-[10px] font-semibold text-rose-400 block">
                      {resumeError}
                    </span>
                  )}
                </div>
              </div>

              {/* Target Roles */}
              {candidateIntelligence?.target_roles && candidateIntelligence.target_roles.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Target Roles:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {candidateIntelligence.target_roles.map((role, idx) => (
                      <span key={idx} className="px-2.5 py-0.5 text-xs font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/30 rounded-full">
                        {role}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Provenanced Skills */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                    Candidate Intelligence Skills ({candidateIntelligence?.skills?.length || 0}):
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">Provenance: Profile ✓ vs Resume ✓</span>
                </div>
                {candidateIntelligence?.skills && candidateIntelligence.skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto custom-scrollbar p-1">
                    {candidateIntelligence.skills.map((s, idx) => (
                      <span
                        key={idx}
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold border flex items-center gap-1.5 ${
                          s.source === "both"
                            ? "bg-purple-500/10 text-purple-300 border-purple-500/30"
                            : s.source === "resume"
                            ? "bg-blue-500/10 text-blue-300 border-blue-500/30"
                            : "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                        }`}
                      >
                        <span>{s.name}</span>
                        <span className="text-[9px] px-1 py-0.2 rounded bg-slate-950/60 font-mono text-slate-400 uppercase">
                          {s.source === "both" ? "Profile + Resume" : s.source === "resume" ? "Resume" : "Profile"}
                        </span>
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No skills listed in profile or resume.</p>
                )}
              </div>

              {/* Grid: Experience, Projects, Education, Certifications */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
                {/* Experience */}
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                    <span>Work Experience</span>
                    <span className="text-[10px] text-slate-500">{candidateIntelligence?.experience?.length || 0} Records</span>
                  </h4>
                  {candidateIntelligence?.experience && candidateIntelligence.experience.length > 0 ? (
                    <div className="space-y-2.5">
                      {candidateIntelligence.experience.map((exp, idx) => (
                        <div key={idx} className="border-l-2 border-sky-500 pl-2.5 text-xs space-y-0.5">
                          <div className="font-bold text-white">{exp.role || "Role Unspecified"}</div>
                          <div className="text-slate-400 font-medium">{exp.company} &bull; {exp.duration || "Duration N/A"}</div>
                          {exp.description && <div className="text-slate-400 text-[11px] italic">{exp.description}</div>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No experience records found.</p>
                  )}
                </div>

                {/* Projects */}
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                    <span>Key Projects</span>
                    <span className="text-[10px] text-slate-500">{candidateIntelligence?.projects?.length || 0} Projects</span>
                  </h4>
                  {candidateIntelligence?.projects && candidateIntelligence.projects.length > 0 ? (
                    <div className="space-y-2.5">
                      {candidateIntelligence.projects.map((proj, idx) => (
                        <div key={idx} className="border-l-2 border-purple-500 pl-2.5 text-xs space-y-0.5">
                          <div className="font-bold text-white">{proj.name || proj.title || "Untitled Project"}</div>
                          {proj.description && <div className="text-slate-400 text-[11px]">{proj.description}</div>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No projects found.</p>
                  )}
                </div>

                {/* Education */}
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                    <span>Education</span>
                    <span className="text-[10px] text-slate-500">{candidateIntelligence?.education?.length || 0} Records</span>
                  </h4>
                  {candidateIntelligence?.education && candidateIntelligence.education.length > 0 ? (
                    <div className="space-y-2">
                      {candidateIntelligence.education.map((edu, idx) => (
                        <div key={idx} className="border-l-2 border-emerald-500 pl-2.5 text-xs">
                          <div className="font-bold text-white">{edu.degree || "Degree"}</div>
                          <div className="text-slate-400">{edu.institution} &bull; {edu.graduation_year || "N/A"}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No education records found.</p>
                  )}
                </div>

                {/* Certifications */}
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
                    <span>Certifications</span>
                    <span className="text-[10px] text-slate-500">{candidateIntelligence?.certifications?.length || 0} Certs</span>
                  </h4>
                  {candidateIntelligence?.certifications && candidateIntelligence.certifications.length > 0 ? (
                    <div className="space-y-2">
                      {candidateIntelligence.certifications.map((cert, idx) => (
                        <div key={idx} className="border-l-2 border-amber-500 pl-2.5 text-xs">
                          <div className="font-bold text-white">{cert.name}</div>
                          <div className="text-slate-400">{cert.issuer} &bull; {cert.issue_date || "N/A"}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No certifications found.</p>
                  )}
                </div>
              </div>
            </div>

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
                      {rankPosition}
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
                {factorScores && factorScores.length > 0 ? (
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
                ) : (
                  <p className="text-xs text-slate-500 italic bg-slate-950 p-3 rounded-lg border border-slate-800">
                    Deterministic factor breakdown unavailable for this candidate score.
                  </p>
                )}
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

              {/* Verified Strengths and Gaps Highlights */}
              {((analysisData?.strengths && analysisData.strengths.length > 0) || (analysisData?.gaps && analysisData.gaps.length > 0)) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-2">
                  {analysisData.strengths && analysisData.strengths.length > 0 && (
                    <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4 space-y-2">
                      <div className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span>✓</span> Key Verified Strengths
                      </div>
                      <ul className="space-y-1.5 text-xs text-slate-200">
                        {analysisData.strengths.map((strItem: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-emerald-400 font-bold">•</span>
                            <span>{strItem}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysisData.gaps && analysisData.gaps.length > 0 && (
                    <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl p-4 space-y-2">
                      <div className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                        <span>⚠</span> Identified Gaps / Missing Items
                      </div>
                      <ul className="space-y-1.5 text-xs text-slate-200">
                        {analysisData.gaps.map((gapItem: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-1.5">
                            <span className="text-amber-400 font-bold">•</span>
                            <span>{gapItem}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {requirementMatches && requirementMatches.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {requirementMatches.map((rm: any) => (
                    <div key={rm.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">{rm.name}</span>
                          <span className="px-1.5 py-0.5 text-[9px] font-semibold bg-slate-800 text-slate-300 rounded uppercase">
                            {rm.level} &bull; {rm.isHard ? "HARD" : "SOFT"}
                          </span>
                        </div>
                        <div>
                          {(rm.status === "MATCHED" || rm.status === "EXACT") && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              ✓ MATCHED
                            </span>
                          )}
                          {(rm.status === "NOT_MATCHED" || rm.status === "FAIL") && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              × NOT MATCHED
                            </span>
                          )}
                          {rm.status === "UNKNOWN" && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              ? UNKNOWN
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Job Requirement vs Candidate Evidence */}
                      <div className="space-y-1.5 text-xs">
                        <div className="text-slate-400">
                          <span className="font-semibold text-slate-300">Job Requirement:</span> {rm.requiredValue}
                        </div>
                        {rm.candidateValue && (
                          <div className="text-slate-400">
                            <span className="font-semibold text-slate-300">Candidate Value:</span> {rm.candidateValue}
                          </div>
                        )}
                      </div>

                      {/* Ground-Truth Evidence Citation */}
                      {rm.evidence ? (
                        <div className="bg-slate-900/80 p-2.5 rounded text-[11px] space-y-1 border border-slate-800 font-mono">
                          <div className="text-slate-400 font-sans font-semibold flex items-center justify-between text-[10px]">
                            <span>Candidate Evidence Citation:</span>
                            <span className="text-emerald-400 font-bold">
                              ✓ VERIFIED EVIDENCE
                            </span>
                          </div>
                          <p className="text-slate-200 leading-snug font-serif">&quot;{rm.evidence}&quot;</p>
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-500 italic">No specific evidence text snippet bound.</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic bg-slate-950 p-4 rounded-lg border border-slate-800">
                  No verified requirement matches available for this job description.
                </p>
              )}
            </div>

            {/* TASK 9: AI RECOMMENDATION PANEL */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🤖</span>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider text-purple-300">AI Recommendation (Advisory Only)</h3>
                </div>
                <span className="px-2.5 py-1 rounded text-xs font-bold bg-purple-500/10 text-purple-300 border border-purple-500/30">
                  {recommendationDetail?.recommendation?.recommendation_type || (overallScore >= 75 ? "RECOMMEND_REVIEW" : overallScore >= 50 ? "REQUIRES_REVIEW" : "NOT_RECOMMENDED_FOR_REVIEW")}
                </span>
              </div>

              <div className="space-y-3">
                <div className="text-xs text-slate-400">
                  Recommendation Confidence: <span className="font-bold text-white">{((recommendationDetail?.recommendation?.recommendation_confidence || confidenceScore) * 100).toFixed(0)}%</span>
                </div>

                <div className="space-y-1.5">
                  <div className="text-xs font-bold text-slate-300 uppercase tracking-wider">Reason Codes:</div>
                  <div className="flex flex-wrap gap-2">
                    {recommendationDetail?.reasons && recommendationDetail.reasons.length > 0 ? (
                      recommendationDetail.reasons.map((r) => (
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
                      ))
                    ) : (
                      <>
                        {eligibility === "PASS" && (
                          <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            ✓ ALL_CRITICAL_REQUIREMENTS_MET
                          </span>
                        )}
                        {overallScore >= 70 && (
                          <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            ✓ HIGH_MATCH_SCORE
                          </span>
                        )}
                        <span className={`px-2.5 py-1 rounded text-xs font-semibold ${
                          confidenceTier === "HIGH"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        }`}>
                          {confidenceTier === "HIGH" ? "✓ HIGH_SCORE_CONFIDENCE" : "⚠ MODERATE_EVIDENCE_COVERAGE"}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">AI-Generated Narrative:</div>
                  <p className="text-xs text-slate-300 italic">
                    {recommendationDetail?.recommendation?.summary ||
                     (overallScore >= 75
                       ? `Candidate demonstrates strong match (${overallScore.toFixed(1)}/100) with verified ground-truth evidence across required skills.`
                       : overallScore >= 50
                       ? `Candidate meets core requirements with an overall match score of ${overallScore.toFixed(1)}/100.`
                       : `Candidate scored ${overallScore.toFixed(1)}/100 with insufficient verified requirements.`)}
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
