"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  fetchRecruiterJobs,
  fetchJobDetails,
  fetchJobIntelligence,
  generateCandidateRankings,
  fetchActiveRankings,
  fetchCandidateAnalysis,
  fetchCandidateIntelligence,
  updateApplicationStatus,
  apiFetch,
  JobItemData,
  CandidateRankingItem,
  JobIntelligenceDetailData,
  CandidateIntelligenceData,
} from "@/lib/api";
import {
  Briefcase,
  Sparkles,
  User,
  Users,
  FileText,
  Search,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Building2,
  MapPin,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

interface ApplicantRow {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  headline: string;
  skills: string[];
  submitted_at: string;
  status: string;
  resume_file_path?: string;
}

interface RankedCandidateRow extends ApplicantRow {
  rank_position: number;
  score: number;
  eligibility_status: string;
  confidence_tier: string;
  matched_skills: string[];
  missing_skills: string[];
}

const isValidUUID = (str: string) =>
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(str);

export default function RecruiterAICandidateMatchingPage() {
  const params = useParams();
  const router = useRouter();
  const rawJobId = (params?.id as string) || "";

  const [activeJobs, setActiveJobs] = useState<JobItemData[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [selectedJob, setSelectedJob] = useState<JobItemData | null>(null);
  const [intelligence, setIntelligence] = useState<JobIntelligenceDetailData | null>(null);

  const [applicants, setApplicants] = useState<ApplicantRow[]>([]);
  const [rankedResults, setRankedResults] = useState<RankedCandidateRow[]>([]);

  const [jobLoading, setJobLoading] = useState<boolean>(true);
  const [rankingLoading, setRankingLoading] = useState<boolean>(false);
  const [isRanked, setIsRanked] = useState<boolean>(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [rankingError, setRankingError] = useState<string | null>(null);

  // Phase 5 Explainable Analysis States
  const [selectedAnalysisCandidate, setSelectedAnalysisCandidate] = useState<RankedCandidateRow | null>(null);
  const [analysisDetail, setAnalysisDetail] = useState<any | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Phase 6 Side-by-Side Candidate Comparison States
  const [comparisonSelectedIds, setComparisonSelectedIds] = useState<string[]>([]);
  const [showComparisonModal, setShowComparisonModal] = useState<boolean>(false);
  const [comparisonCandidateDetails, setComparisonCandidateDetails] = useState<Record<string, CandidateIntelligenceData>>({});
  const [comparisonLoading, setComparisonLoading] = useState<boolean>(false);

  const toggleCompareCandidate = (appId: string) => {
    setComparisonSelectedIds((prev) =>
      prev.includes(appId) ? prev.filter((id) => id !== appId) : [...prev, appId]
    );
  };

  const handleOpenComparison = async () => {
    setShowComparisonModal(true);
    setComparisonLoading(true);
    try {
      const selectedApps = (isRanked && rankedResults.length > 0 ? rankedResults : applicants).filter((a) =>
        comparisonSelectedIds.includes(a.id)
      );
      const detailsMap: Record<string, CandidateIntelligenceData> = {};
      for (const app of selectedApps) {
        if (!comparisonCandidateDetails[app.candidate_id]) {
          const intel = await fetchCandidateIntelligence(app.candidate_id);
          if (intel) {
            detailsMap[app.candidate_id] = intel;
          }
        }
      }
      setComparisonCandidateDetails((prev) => ({ ...prev, ...detailsMap }));
    } catch (err) {
      console.error("Failed to load candidate intelligence for comparison:", err);
    } finally {
      setComparisonLoading(false);
    }
  };

  const handleViewResumeFromComparison = async (appId: string) => {
    try {
      const response = await apiFetch(`/api/v1/jobs/applications/${appId}/resume`);
      if (!response.ok) {
        alert("Original resume is unavailable or authentication required.");
        return;
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      window.open(objectUrl, "_blank");
    } catch (err) {
      console.error("Error opening resume PDF:", err);
    }
  };

  const handleOpenAnalysis = async (candidate: RankedCandidateRow) => {
    setSelectedAnalysisCandidate(candidate);
    setAnalysisDetail(null);
    setAnalysisError(null);
    setAnalysisLoading(true);

    try {
      const data = await fetchCandidateAnalysis(selectedJobId, candidate.candidate_id);
      if (data) {
        setAnalysisDetail(data);
      } else {
        setAnalysisError("Analysis not available for selected candidate.");
      }
    } catch (err: any) {
      setAnalysisError(err.message || "Failed to load candidate analysis.");
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleStatusUpdate = async (applicationId: string, newStatus: string) => {
    setApplicants((prev) =>
      prev.map((a) => (a.id === applicationId ? { ...a, status: newStatus } : a))
    );
    setRankedResults((prev) =>
      prev.map((r) => (r.id === applicationId ? { ...r, status: newStatus } : r))
    );
    if (selectedAnalysisCandidate && selectedAnalysisCandidate.id === applicationId) {
      setSelectedAnalysisCandidate((prev) => (prev ? { ...prev, status: newStatus } : null));
    }

    try {
      await updateApplicationStatus(applicationId, newStatus);
    } catch (err: any) {
      console.error("Status update error:", err);
    }
  };

  // Initialize Page & Jobs List
  useEffect(() => {
    async function initPage() {
      setJobLoading(true);
      setPageError(null);
      try {
        const jobs = await fetchRecruiterJobs();
        setActiveJobs(jobs);

        let targetId = rawJobId;
        if (!targetId || !isValidUUID(targetId)) {

          if (jobs.length > 0) {
            targetId = jobs[0].id;
          } else {
            setJobLoading(false);
            return;
          }
        }

        setSelectedJobId(targetId);
        await handleSelectJob(targetId);
      } catch (err: any) {
        console.error("Error initializing AI matching page:", err);
        setPageError(err.message || "Failed to load jobs list.");
        setJobLoading(false);
      }
    }

    initPage();
  }, [rawJobId]);

  // Load Job Details & Applicant Pool when job selection changes
  const handleSelectJob = async (jobId: string) => {
    setSelectedJobId(jobId);
    setJobLoading(true);
    setPageError(null);
    setIntelligence(null); // Clear previous job intelligence state immediately

    // Reset ranking & analysis state immediately upon job switch
    setRankedResults([]);
    setIsRanked(false);
    setRankingError(null);
    setSelectedAnalysisCandidate(null);
    setAnalysisDetail(null);
    setAnalysisError(null);

    // Reset Phase 6 Comparison state immediately upon job switch
    setComparisonSelectedIds([]);
    setShowComparisonModal(false);
    setComparisonCandidateDetails({});

    try {
      // 1. Load Job Details
      const jobData = await fetchJobDetails(jobId);
      setSelectedJob(jobData);

      // 2. Load Job Intelligence
      let intelData: JobIntelligenceDetailData | null = null;
      try {
        intelData = await fetchJobIntelligence(jobId);
        setIntelligence(intelData);
      } catch (e) {
        console.warn("Could not fetch job intelligence for job:", jobId, e);
      }

      // 2. Load Job Applicants Pool
      const appRes = await apiFetch(`/api/v1/jobs/${jobId}/applications`);
      let formatted: ApplicantRow[] = [];
      if (appRes.ok) {
          const body = await appRes.json();
          const rawApps: any[] = Array.isArray(body) ? body : body.items || [];
          formatted = rawApps.map((a) => ({
            id: a.id,
            candidate_id: a.candidate_id,
            candidate_name: a.candidate_name || a.candidate_email || `Candidate ${a.candidate_id.substring(0, 8)}`,
            candidate_email: a.candidate_email || "candidate@example.com",
            headline: a.headline || "Applicant",
            skills: a.skills && a.skills.length > 0 ? a.skills : ["Python", "FastAPI", "Machine Learning"],
            submitted_at: a.created_at || a.submitted_at || new Date().toISOString(),
            status: a.status || "SUBMITTED",
            resume_file_path: a.resume_file_path,
          }));
          setApplicants(formatted);
        } else {
          setApplicants([]);
        }

        // 3. Automatically check if AI rankings already exist for this job
        try {
          const rankingVer = await fetchActiveRankings(jobId);
          const rankingItems: CandidateRankingItem[] = rankingVer?.rankings || [];
          if (formatted.length > 0) {
            const rankMap = new Map<string, CandidateRankingItem>();
            rankingItems.forEach((r) => {
              if (r.candidate_id) rankMap.set(r.candidate_id, r);
              if (r.application_id) rankMap.set(r.application_id, r);
            });

            const reqSkills: string[] = [
              ...(intelData?.extracted_data?.required_skills || []),
              ...((intelData?.requirements || []).map((rq: any) => rq.canonical_value || rq.requirement_name || rq.name || "")),
              ...(jobData?.skills || []),
            ].filter((s) => Boolean(s) && typeof s === "string" && s.trim().length > 0);

            const jobTextLower = ((jobData?.description || "") + " " + (jobData?.title || "")).toLowerCase();

            const calculated: RankedCandidateRow[] = formatted.map((app) => {
              const r = rankMap.get(app.candidate_id) || rankMap.get(app.id);
              const candSkillsLower = app.skills.map((s) => s.toLowerCase().trim());

              const matched_skills = app.skills.filter((s) => {
                const sLower = s.toLowerCase().trim();
                return reqSkills.some((req) => req.toLowerCase().includes(sLower) || sLower.includes(req.toLowerCase())) ||
                       jobTextLower.includes(sLower);
              });

              const missing_skills = reqSkills.filter((req) => {
                const reqLower = req.toLowerCase().trim();
                return !candSkillsLower.some((candSkill) => candSkill.includes(reqLower) || reqLower.includes(candSkill));
              });

              let score = r ? Number(r.score) : 0.0;
              if ((!r || score === 0) && reqSkills.length > 0 && matched_skills.length > 0) {
                const matchRatio = matched_skills.length / reqSkills.length;
                score = Math.round(matchRatio * 100);
              }

              const eligibility = r ? r.eligibility_status : (score >= 50 ? "PASS" : "FAIL");
              const confidence = r
                ? r.score_confidence >= 0.85
                  ? "HIGH"
                  : r.score_confidence >= 0.70
                  ? "MEDIUM"
                  : "LOW"
                : (score >= 70 ? "HIGH" : score >= 40 ? "MEDIUM" : "LOW");

              return {
                ...app,
                rank_position: r ? r.rank_position : 0,
                score,
                eligibility_status: eligibility,
                confidence_tier: confidence,
                matched_skills,
                missing_skills,
              };
            });

            calculated.sort((a, b) => b.score - a.score);
            setRankedResults(calculated);
            setIsRanked(true);
          }
        } catch (e) {
          console.warn("No previous ranking snapshot found for job:", jobId, e);
        }
      } catch (err: any) {
        console.error("Error loading job details or applicants:", err);
        setPageError(err.message || "Failed to load job details or applicants.");
      } finally {
        setJobLoading(false);
      }
    };

  // Manual Trigger: SEARCH & RANK CANDIDATES
  const handleSearchAndRank = async () => {
    if (!selectedJobId || applicants.length === 0) return;

    setRankingLoading(true);
    setRankingError(null);

    try {
      // 1. Call AI Ranking Generation endpoint
      await generateCandidateRankings(selectedJobId, 50);

      // 2. Fetch calculated rankings snapshot
      const rankingVer = await fetchActiveRankings(selectedJobId);
      const rankingItems: CandidateRankingItem[] = rankingVer?.rankings || [];

      // Create lookup map by candidate_id and application_id
      const rankMap = new Map<string, CandidateRankingItem>();
      rankingItems.forEach((r) => {
        if (r.candidate_id) rankMap.set(r.candidate_id, r);
        if (r.application_id) rankMap.set(r.application_id, r);
      });

      // 3. Extract job requirements
      const reqSkills: string[] = [
        ...(intelligence?.extracted_data?.required_skills || []),
        ...((intelligence?.requirements || []).map((rq: any) => rq.canonical_value || rq.requirement_name || rq.name || "")),
        ...(selectedJob?.skills || []),
      ].filter((s) => Boolean(s) && typeof s === "string" && s.trim().length > 0);

      const jobTextLower = ((selectedJob?.description || "") + " " + (selectedJob?.title || "")).toLowerCase();

      // 4. Map applicants with AI scores & sort DESC by match score
      const calculated: RankedCandidateRow[] = applicants.map((app) => {
        const r = rankMap.get(app.candidate_id) || rankMap.get(app.id);
        const candSkillsLower = app.skills.map((s) => s.toLowerCase().trim());

        const matched_skills = app.skills.filter((s) => {
          const sLower = s.toLowerCase().trim();
          return reqSkills.some((req) => req.toLowerCase().includes(sLower) || sLower.includes(req.toLowerCase())) ||
                 jobTextLower.includes(sLower);
        });

        const missing_skills = reqSkills.filter((req) => {
          const reqLower = req.toLowerCase().trim();
          return !candSkillsLower.some((candSkill) => candSkill.includes(reqLower) || reqLower.includes(candSkill));
        });

        let score = r ? Number(r.score) : 0.0;
        if ((!r || score === 0) && reqSkills.length > 0 && matched_skills.length > 0) {
          const matchRatio = matched_skills.length / reqSkills.length;
          score = Math.round(matchRatio * 100);
        }

        const eligibility = r ? r.eligibility_status : (score >= 50 ? "PASS" : "FAIL");
        const confidence = r
          ? r.score_confidence >= 0.85
            ? "HIGH"
            : r.score_confidence >= 0.70
            ? "MEDIUM"
            : "LOW"
          : (score >= 70 ? "HIGH" : score >= 40 ? "MEDIUM" : "LOW");

        return {
          ...app,
          rank_position: r ? r.rank_position : 0,
          score,
          eligibility_status: eligibility,
          confidence_tier: confidence,
          matched_skills,
          missing_skills,
        };
      });

      // Sort DESC by match_score
      calculated.sort((a, b) => b.score - a.score);

      // Assign 1-based serial numbers #1, #2, #3...
      const finalRanked = calculated.map((item, index) => ({
        ...item,
        rank_position: index + 1,
      }));

      setRankedResults(finalRanked);
      setIsRanked(true);
    } catch (err: any) {
      console.error("Error executing AI candidate search & ranking:", err);
      setRankingError(err.message || "AI ranking could not be generated. Please try again.");
    } finally {
      setRankingLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-4 md:p-6 font-sans">
      <div className="max-w-[1600px] mx-auto space-y-6">
        {/* ============================================================ */}
        {/* TOP HEADER */}
        {/* ============================================================ */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-[#111a2c] border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-sky-400 font-medium">
              <Link href="/recruiter/jobs" className="hover:underline flex items-center gap-1">
                &larr; Recruiter Dashboard
              </Link>
              <span>/</span>
              <span>AI Matching Workspace</span>
            </div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
              <Sparkles className="text-sky-400" size={24} /> AI Candidate Search & Ranking
            </h1>
            <p className="text-slate-400 text-xs">
              Select a job, review applicants, and run AI-powered candidate matching.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Job Selector Dropdown */}
            <div className="flex items-center gap-2.5 bg-[#0b1425] border border-slate-700/80 rounded-xl px-3.5 py-2.5 shadow-inner">
              <Briefcase size={16} className="text-sky-400" />
              <span className="text-xs text-slate-400 font-semibold">Job:</span>
              <select
                value={selectedJobId}
                onChange={(e) => handleSelectJob(e.target.value)}
                className="bg-transparent text-xs text-white font-bold outline-none cursor-pointer pr-2"
                disabled={activeJobs.length === 0}
              >
                {activeJobs.length === 0 ? (
                  <option value="">No Active Jobs Available</option>
                ) : (
                  activeJobs.map((j) => (
                    <option key={j.id} value={j.id} className="bg-[#0b1425] text-white">
                      {j.title} ({j.status})
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Primary Action Button: SEARCH & RANK CANDIDATES */}
            <button
              onClick={handleSearchAndRank}
              disabled={!selectedJobId || applicants.length === 0 || rankingLoading}
              className={`px-5 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 transition shadow-lg ${
                !selectedJobId || applicants.length === 0
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                  : rankingLoading
                  ? "bg-sky-700 text-sky-100 cursor-wait border border-sky-500/50"
                  : isRanked
                  ? "bg-indigo-600 hover:bg-indigo-500 text-white border border-indigo-400/50"
                  : "bg-sky-600 hover:bg-sky-500 text-white border border-sky-400/50"
              }`}
            >
              {rankingLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-sky-200 border-t-transparent rounded-full animate-spin" />
                  <span>ANALYZING CANDIDATES...</span>
                </>
              ) : isRanked ? (
                <>
                  <Sparkles size={15} />
                  <span>RE-RUN AI RANKING</span>
                </>
              ) : (
                <>
                  <Search size={15} />
                  <span>SEARCH & RANK CANDIDATES</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        {pageError && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-xl text-xs font-bold flex items-center justify-between">
            <span>⚠️ {pageError}</span>
            <button onClick={() => setPageError(null)} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {/* ============================================================ */}
        {/* THREE-COLUMN WORKSPACE LAYOUT */}
        {/* ============================================================ */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* ============================================================ */}
          {/* COLUMN 1 — JOB DETAILS (LEFT PANEL, 4 COLS) */}
          {/* ============================================================ */}
          <div className="lg:col-span-4 bg-[#111a2c] border border-slate-800 rounded-2xl flex flex-col h-[780px] overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 bg-[#0b1425] flex items-center justify-between">
              <div>
                <h2 className="font-bold text-white text-sm flex items-center gap-2">
                  <Briefcase size={16} className="text-sky-400" /> JOB DESCRIPTION
                </h2>
                <p className="text-[11px] text-slate-400">Selected Job Requirements & Scope</p>
              </div>
              {selectedJob && (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  {selectedJob.status}
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {jobLoading ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-xs font-semibold">
                  <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mr-2" />
                  Loading job details...
                </div>
              ) : !selectedJob ? (
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-2 text-slate-400">
                  <Briefcase size={32} className="text-slate-600 mb-1" />
                  <p className="font-bold text-slate-300 text-xs">Select a job to view requirements.</p>
                  <p className="text-[11px] text-slate-500">Choose a job from the top dropdown selector.</p>
                </div>
              ) : (
                <>
                  {/* 1. ROLE / TITLE */}
                  <div className="space-y-1">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-sky-400">Role / Title</span>
                    <h3 className="text-lg font-bold text-white">
                      {intelligence?.extracted_data?.role_title || selectedJob.title}
                    </h3>
                  </div>

                  <div className="grid grid-cols-2 gap-2 bg-[#0b1425] p-3 rounded-xl border border-slate-800 text-xs">
                    <div>
                      <span className="text-slate-500 block text-[10px] font-semibold">Department</span>
                      <span className="text-slate-200 font-bold">{selectedJob.department || "Engineering"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px] font-semibold">Location</span>
                      <span className="text-slate-200 font-bold">{selectedJob.location || "Remote"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px] font-semibold">Employment Type</span>
                      <span className="text-slate-200 font-bold">{selectedJob.employment_type || "FULL_TIME"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block text-[10px] font-semibold">Verification</span>
                      <span className="text-emerald-400 font-bold">{selectedJob.verification_status}</span>
                    </div>
                  </div>

                  {/* 2. REQUIRED SKILLS */}
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-slate-300">Required Skills</h4>
                    {(() => {
                      const reqSkills =
                        intelligence?.extracted_data?.required_skills ||
                        (intelligence?.requirements || [])
                          .filter((r: any) => r.requirement_level?.toUpperCase() === "REQUIRED" || r.requirement_level === "REQUIRED")
                          .map((r: any) => r.canonical_value);
                      if (reqSkills.length > 0) {
                        return (
                          <div className="flex flex-wrap gap-1.5">
                            {reqSkills.map((skill: string, idx: number) => (
                              <span
                                key={idx}
                                className="px-2.5 py-1 bg-sky-500/10 border border-sky-500/30 text-sky-300 rounded-lg text-[11px] font-bold"
                              >
                                • {skill}
                              </span>
                            ))}
                          </div>
                        );
                      }
                      return <p className="text-[11px] text-slate-500 italic">None specified in job description</p>;
                    })()}
                  </div>

                  {/* 5. PREFERRED SKILLS */}
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-slate-300">Preferred Skills</h4>
                    {(() => {
                      const prefSkills =
                        intelligence?.extracted_data?.preferred_skills ||
                        (intelligence?.requirements || [])
                          .filter((r: any) => r.requirement_level?.toUpperCase() === "PREFERRED" || r.requirement_level === "PREFERRED")
                          .map((r: any) => r.canonical_value);
                      if (prefSkills.length > 0) {
                        return (
                          <div className="flex flex-wrap gap-1.5">
                            {prefSkills.map((skill: string, idx: number) => (
                              <span
                                key={idx}
                                className="px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-lg text-[11px] font-bold"
                              >
                                • {skill}
                              </span>
                            ))}
                          </div>
                        );
                      }
                      return <p className="text-[11px] text-slate-500 italic">None specified in job description</p>;
                    })()}
                  </div>

                  {/* 6. GOOD TO HAVE */}
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-slate-300">Good to Have</h4>
                    {(() => {
                      const gthSkills =
                        intelligence?.extracted_data?.good_to_have ||
                        (intelligence?.requirements || [])
                          .filter((r: any) => r.requirement_level?.toUpperCase() === "NICE_TO_HAVE" || r.requirement_level === "NICE_TO_HAVE")
                          .map((r: any) => r.canonical_value);
                      if (gthSkills.length > 0) {
                        return (
                          <div className="flex flex-wrap gap-1.5">
                            {gthSkills.map((skill: string, idx: number) => (
                              <span
                                key={idx}
                                className="px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-lg text-[11px] font-bold"
                              >
                                • {skill}
                              </span>
                            ))}
                          </div>
                        );
                      }
                      return <p className="text-[11px] text-slate-500 italic">None specified in job description</p>;
                    })()}
                  </div>



                  {/* 4. RESPONSIBILITIES */}
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-slate-300">Responsibilities</h4>
                    {intelligence?.extracted_data?.responsibilities && intelligence.extracted_data.responsibilities.length > 0 ? (
                      <div className="bg-[#0b1425] p-3 rounded-xl border border-slate-800 text-[11px] text-slate-300 space-y-1">
                        {intelligence.extracted_data.responsibilities.map((resp: string, idx: number) => (
                          <p key={idx} className="flex items-start gap-1.5">
                            <span className="text-sky-400 font-bold">•</span>
                            <span>{resp}</span>
                          </p>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[11px] text-slate-500 italic">None specified in job description</p>
                    )}
                  </div>

                  {/* Original Job Description */}
                  <div className="space-y-1.5 pt-2">
                    <h4 className="text-xs font-bold text-slate-300">Original Job Description</h4>
                    <div className="bg-[#0b1425] p-3.5 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed whitespace-pre-line font-mono text-[11px]">
                      {selectedJob.description}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ============================================================ */}
          {/* COLUMN 2 — APPLICANTS (MIDDLE PANEL, 4 COLS) */}
          {/* ============================================================ */}
          <div className="lg:col-span-4 bg-[#111a2c] border border-slate-800 rounded-2xl flex flex-col h-[780px] overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 bg-[#0b1425] flex items-center justify-between">
              <div>
                <h2 className="font-bold text-white text-sm flex items-center gap-2">
                  <Users size={16} className="text-indigo-400" /> CANDIDATES WHO APPLIED
                </h2>
                <p className="text-[11px] text-slate-400">Raw Applicant Pool for Selected Job</p>
              </div>
              <div className="flex items-center gap-2">
                {comparisonSelectedIds.length > 0 && (
                  <button
                    onClick={handleOpenComparison}
                    className="px-2.5 py-1 bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs rounded-lg border border-purple-400 flex items-center gap-1 shadow transition"
                  >
                    Compare ({comparisonSelectedIds.length})
                  </button>
                )}
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {applicants.length} Applicants
                </span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              {jobLoading ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-xs font-semibold">
                  <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin mr-2" />
                  Loading applicant pool...
                </div>
              ) : !selectedJobId ? (
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-2 text-slate-400">
                  <Users size={32} className="text-slate-600 mb-1" />
                  <p className="font-bold text-slate-300 text-xs">Select a job to view applicants.</p>
                  <p className="text-[11px] text-slate-500">Applicant pool will load automatically.</p>
                </div>
              ) : applicants.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-2 text-slate-400">
                  <Users size={32} className="text-slate-600 mb-1" />
                  <p className="font-bold text-slate-300 text-xs">No candidates have applied to this job yet.</p>
                  <p className="text-[11px] text-slate-500">
                    When candidates submit applications, they will appear here.
                  </p>
                </div>
              ) : (
                applicants.map((app, index) => (
                  <div
                    key={app.id}
                    className={`bg-[#0b1425] border rounded-xl p-3.5 space-y-2.5 transition ${
                      comparisonSelectedIds.includes(app.id) ? "border-purple-500/80 bg-purple-500/5" : "border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={comparisonSelectedIds.includes(app.id)}
                          onChange={() => toggleCompareCandidate(app.id)}
                          className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-purple-600 focus:ring-purple-500 cursor-pointer"
                        />
                        <span className="w-6 h-6 rounded-full bg-slate-800 text-slate-300 font-bold text-[11px] flex items-center justify-center border border-slate-700">
                          {index + 1}
                        </span>
                        <div>
                          <h4 className="font-bold text-white text-xs">{app.candidate_name}</h4>
                          <p className="text-[11px] text-slate-400 font-medium">{app.headline}</p>
                        </div>
                      </div>
                      <select
                        value={app.status}
                        onChange={(e) => handleStatusUpdate(app.id, e.target.value)}
                        className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#111a2c] text-sky-300 border border-sky-500/30 outline-none cursor-pointer"
                      >
                        <option value="SUBMITTED" className="bg-[#0b1425] text-white">SUBMITTED</option>
                        <option value="REVIEWED" className="bg-[#0b1425] text-white">REVIEWED</option>
                        <option value="SHORTLISTED" className="bg-[#0b1425] text-white">SHORTLISTED</option>
                        <option value="INTERVIEW" className="bg-[#0b1425] text-white">INTERVIEW</option>
                        <option value="SELECTED" className="bg-[#0b1425] text-white">SELECTED</option>
                        <option value="REJECTED" className="bg-[#0b1425] text-white">REJECTED</option>
                      </select>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-0.5 pl-8">
                      <p>✉ {app.candidate_email}</p>
                      <p>📅 Applied: {new Date(app.submitted_at).toLocaleDateString()}</p>
                    </div>

                    <div className="pl-8 flex flex-wrap gap-1">
                      {app.skills.slice(0, 4).map((s, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-[10px] font-medium border border-slate-700"
                        >
                          {s}
                        </span>
                      ))}
                    </div>

                    <div className="pl-8 pt-1 flex items-center justify-between text-[11px]">
                      <button
                        onClick={() => handleViewResumeFromComparison(app.id)}
                        className="text-emerald-400 hover:text-emerald-300 font-bold flex items-center gap-1 hover:underline cursor-pointer"
                        title="View & Download Candidate Resume PDF"
                      >
                        <FileText size={12} /> View Resume PDF
                      </button>
                      <Link
                        href={`/recruiter/jobs/${selectedJobId}/applications/${app.id}`}
                        className="text-sky-400 hover:underline font-semibold flex items-center gap-0.5"
                      >
                        Inspect &rarr;
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ============================================================ */}
          {/* COLUMN 3 — AI RANKING (RIGHT PANEL, 4 COLS) */}
          {/* ============================================================ */}
          <div className="lg:col-span-4 bg-[#111a2c] border border-slate-800 rounded-2xl flex flex-col h-[780px] overflow-hidden shadow-xl">
            <div className="p-4 border-b border-slate-800 bg-[#0b1425] flex items-center justify-between">
              <div>
                <h2 className="font-bold text-white text-sm flex items-center gap-2">
                  <Sparkles size={16} className="text-amber-400" /> AI RANKING
                </h2>
                <p className="text-[11px] text-slate-400">Match Scores Sorted Descending</p>
              </div>
              {isRanked && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {rankedResults.length} Ranked
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
              {rankingLoading ? (
                /* LOADING STATE */
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-3">
                  <div className="w-8 h-8 border-3 border-sky-400 border-t-transparent rounded-full animate-spin" />
                  <div className="space-y-1">
                    <p className="font-bold text-white text-xs">AI Candidate Analysis Running</p>
                    <p className="text-[11px] text-slate-400">
                      Analyzing {applicants.length} applicant(s) against{" "}
                      <span className="text-sky-300 font-semibold">{selectedJob?.title}</span>...
                    </p>
                  </div>
                </div>
              ) : !selectedJobId ? (
                /* UNSELECTED JOB STATE */
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-2 text-slate-400">
                  <Sparkles size={32} className="text-slate-600 mb-1" />
                  <p className="font-bold text-slate-300 text-xs">Select a job and run AI ranking.</p>
                  <p className="text-[11px] text-slate-500">AI match scores will appear here.</p>
                </div>
              ) : applicants.length === 0 ? (
                /* ZERO APPLICANTS STATE */
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-2 text-slate-400">
                  <AlertCircle size={32} className="text-slate-600 mb-1" />
                  <p className="font-bold text-slate-300 text-xs">AI ranking cannot be generated.</p>
                  <p className="text-[11px] text-slate-500">
                    There are currently no applicants for this job.
                  </p>
                </div>
              ) : !isRanked ? (
                /* UNRANKED INITIAL STATE BEFORE SEARCH BUTTON CLICK */
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-3 bg-[#0b1425]/50 rounded-xl border border-dashed border-slate-800">
                  <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-inner">
                    <Sparkles size={24} />
                  </div>
                  <div className="space-y-1.5 max-w-xs">
                    <h3 className="font-bold text-white text-xs">AI Ranking Not Generated</h3>
                    <p className="text-[11px] text-slate-400 leading-normal">
                      Review the applicants and click{" "}
                      <span className="text-sky-400 font-bold">SEARCH & RANK CANDIDATES</span> to evaluate the
                      applicants.
                    </p>
                  </div>
                  <button
                    onClick={handleSearchAndRank}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-xl shadow border border-sky-400/50 flex items-center gap-1.5 transition"
                  >
                    <Search size={14} /> SEARCH & RANK CANDIDATES
                  </button>
                </div>
              ) : rankingError ? (
                /* ERROR STATE */
                <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-3">
                  <XCircle size={32} className="text-rose-400" />
                  <p className="font-bold text-rose-300 text-xs bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl">
                    {rankingError}
                  </p>
                  <button
                    onClick={handleSearchAndRank}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-lg border border-slate-700"
                  >
                    Try Again
                  </button>
                </div>
              ) : (
                /* RANKED RESULTS DISPLAY (SORTED DESC) */
                rankedResults.map((r) => (
                  <div
                    key={r.id}
                    className="bg-[#0b1425] border border-amber-500/30 rounded-xl p-3.5 space-y-2.5 shadow-md relative overflow-hidden"
                  >
                    {/* Rank Badge Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 font-extrabold text-xs border border-amber-500/40">
                          #{r.rank_position}
                        </span>
                        <div>
                          <h4 className="font-bold text-white text-xs">{r.candidate_name}</h4>
                          <p className="text-[10px] text-slate-400">{r.headline}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-base font-extrabold text-amber-400 block leading-tight">
                          {r.score} <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
                        </span>
                        <span className="text-[10px] text-slate-500 font-medium">Match Score</span>
                      </div>
                    </div>

                    {/* Eligibility & Confidence Badges */}
                    <div className="flex items-center gap-2 pt-1">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.eligibility_status === "PASS"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        }`}
                      >
                        {r.eligibility_status === "PASS" ? "✓ Eligibility: PASS" : "✕ Eligibility: NOT ELIGIBLE"}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                        Confidence: {r.confidence_tier}
                      </span>
                    </div>

                    {/* Evidence Match Breakdown */}
                    <div className="bg-[#111a2c] p-2.5 rounded-lg border border-slate-800 text-[11px] space-y-1.5">
                      <div className="text-emerald-400 font-semibold flex flex-wrap gap-1 items-center">
                        <span className="text-[11px]">✓ Matched:</span>
                        {r.matched_skills && r.matched_skills.length > 0 ? (
                          r.matched_skills.map((s, idx) => (
                            <span key={idx} className="bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded text-[10px]">
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-400 font-normal italic text-[10px]">None matched</span>
                        )}
                      </div>
                      <div className="text-amber-400/90 font-medium flex flex-wrap gap-1 items-center pt-0.5">
                        <span className="text-[11px] font-semibold text-amber-400">⚠ Skill Gaps:</span>
                        {r.missing_skills && r.missing_skills.length > 0 ? (
                          r.missing_skills.slice(0, 4).map((s, idx) => (
                            <span key={idx} className="bg-amber-500/10 border border-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded text-[10px]">
                              {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-emerald-400 font-normal text-[10px]">No major skill gaps</span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/80">
                      <button
                        onClick={() => handleOpenAnalysis(r)}
                        className="px-2.5 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-bold rounded-lg border border-amber-500/40 flex items-center gap-1 transition"
                      >
                        <Sparkles size={12} /> Analyze Match
                      </button>
                      <Link
                        href={`/recruiter/jobs/${selectedJobId}/applications/${r.id}`}
                        className="text-sky-400 hover:underline font-semibold flex items-center gap-0.5"
                      >
                        Inspect Candidate &rarr;
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* PHASE 5 — EXPLAINABLE AI CANDIDATE ANALYSIS MODAL */}
        {/* ============================================================ */}
        {selectedAnalysisCandidate && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#111a2c] border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
              {/* Modal Header */}
              <div className="p-5 border-b border-slate-800 bg-[#0b1425] flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 text-xs text-amber-400 font-bold uppercase tracking-wider">
                    <Sparkles size={16} /> Phase 5 Explainable Match Analysis
                  </div>
                  <h2 className="text-xl font-bold text-white mt-0.5">
                    {selectedAnalysisCandidate.candidate_name}
                  </h2>
                  <p className="text-xs text-slate-400">
                    Application ID: <span className="font-mono text-slate-300">{selectedAnalysisCandidate.id}</span>
                  </p>
                </div>
                <button
                  onClick={() => {
                    setSelectedAnalysisCandidate(null);
                    setAnalysisDetail(null);
                  }}
                  className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold flex items-center justify-center border border-slate-700 transition"
                >
                  ✕
                </button>
              </div>

              {/* Modal Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                {analysisLoading ? (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-400 space-y-3">
                    <div className="w-8 h-8 border-3 border-amber-400 border-t-transparent rounded-full animate-spin" />
                    <p className="font-bold text-xs">Loading Phase 5 Explainable Match Analysis...</p>
                  </div>
                ) : analysisError ? (
                  <div className="bg-rose-500/10 border border-rose-500/30 p-4 rounded-xl text-rose-300 text-xs font-bold">
                    ⚠️ {analysisError}
                  </div>
                ) : analysisDetail ? (
                  <>
                    {/* Score Banner (Phase 3 == Phase 4 == Phase 5) & Recruiter Decision Control */}
                    <div className="bg-[#0b1425] border border-slate-800 rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Phase 3 Match Score</span>
                        <div className="text-3xl font-extrabold text-amber-400 mt-0.5">
                          {analysisDetail.overall_score.toFixed(1)} <span className="text-sm font-normal text-slate-500">/ 100</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-3">
                        <span className={`px-3 py-1 rounded-lg text-xs font-extrabold border ${
                          analysisDetail.eligibility_status === "PASS"
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                            : "bg-rose-500/20 text-rose-300 border-rose-500/40"
                        }`}>
                          ✓ Eligibility: {analysisDetail.eligibility_status}
                        </span>

                        {/* Recruiter Application Status Selector */}
                        <div className="flex items-center gap-1.5 bg-[#111a2c] border border-indigo-500/40 rounded-xl px-3 py-1.5 shadow-inner">
                          <span className="text-[10px] text-indigo-300 font-bold uppercase tracking-wider">Recruiter Status:</span>
                          <select
                            value={selectedAnalysisCandidate.status}
                            onChange={(e) => handleStatusUpdate(selectedAnalysisCandidate.id, e.target.value)}
                            className="bg-transparent text-xs text-white font-bold outline-none cursor-pointer pr-1"
                          >
                            <option value="SUBMITTED" className="bg-[#0b1425] text-white">SUBMITTED</option>
                            <option value="REVIEWED" className="bg-[#0b1425] text-white">REVIEWED</option>
                            <option value="SHORTLISTED" className="bg-[#0b1425] text-white">SHORTLISTED</option>
                            <option value="INTERVIEW" className="bg-[#0b1425] text-white">INTERVIEW</option>
                            <option value="SELECTED" className="bg-[#0b1425] text-white">SELECTED</option>
                            <option value="REJECTED" className="bg-[#0b1425] text-white">REJECTED</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* 8-Factor Score Breakdown */}
                    <div className="space-y-2">
                      <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">8-Factor Score Breakdown</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
                        {Object.entries(analysisDetail.score_breakdown || {}).map(([key, val]: [string, any]) => {
                          if (key === "weighted_total") return null;
                          return (
                            <div key={key} className="bg-[#0b1425] p-3 rounded-xl border border-slate-800 text-xs">
                              <span className="text-[10px] text-slate-400 font-semibold block capitalize">
                                {key.replace(/_/g, " ")}
                              </span>
                              <span className="text-sm font-extrabold text-white mt-1 block">
                                {typeof val === "number" ? val.toFixed(1) : val}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Strengths & Gaps */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Strengths */}
                      <div className="bg-emerald-500/5 border border-emerald-500/20 p-4 rounded-xl space-y-2">
                        <h4 className="text-xs font-bold text-emerald-400 flex items-center gap-1.5 uppercase">
                          <CheckCircle2 size={14} /> Evidence-Backed Strengths
                        </h4>
                        {analysisDetail.strengths && analysisDetail.strengths.length > 0 ? (
                          <ul className="space-y-1 text-xs text-slate-300 pl-4 list-disc">
                            {analysisDetail.strengths.map((st: string, idx: number) => (
                              <li key={idx}>{st}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-slate-500 italic">No specific strengths flagged</p>
                        )}
                      </div>

                      {/* Gaps */}
                      <div className="bg-amber-500/5 border border-amber-500/20 p-4 rounded-xl space-y-2">
                        <h4 className="text-xs font-bold text-amber-400 flex items-center gap-1.5 uppercase">
                          <AlertCircle size={14} /> Identified Gaps & Missing Requirements
                        </h4>
                        {analysisDetail.gaps && analysisDetail.gaps.length > 0 ? (
                          <ul className="space-y-1 text-xs text-slate-300 pl-4 list-disc">
                            {analysisDetail.gaps.map((gp: string, idx: number) => (
                              <li key={idx}>{gp}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-slate-500 italic">No critical gaps identified</p>
                        )}
                      </div>
                    </div>

                    {/* Matched Requirements with Evidence */}
                    <div className="space-y-2">
                      <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Matched Requirements & Ground-Truth Evidence</h3>
                      <div className="space-y-2">
                        {analysisDetail.matched_requirements && analysisDetail.matched_requirements.length > 0 ? (
                          analysisDetail.matched_requirements.map((m: any, idx: number) => (
                            <div key={idx} className="bg-[#0b1425] p-3 rounded-xl border border-slate-800 text-xs space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-emerald-400">✓ {m.canonical_required_value}</span>
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                                  {m.match_status || "MATCHED"} ({m.match_type || "EXACT"})
                                </span>
                              </div>
                              {m.evidence_text && (
                                  <p className="text-[11px] text-slate-400 bg-[#111a2c] p-2 rounded-lg border border-slate-800/60 font-mono">
                                    Evidence: &quot;{m.evidence_text}&quot;
                                  </p>
                              )}
                            </div>
                          ))
                        ) : (
                          <p className="text-xs text-slate-500 italic">No matched requirements found.</p>
                        )}
                      </div>
                    </div>
                  </>
                ) : null}
              </div>

              {/* Modal Footer */}
              <div className="p-4 border-t border-slate-800 bg-[#0b1425] flex justify-end">
                <button
                  onClick={() => {
                    setSelectedAnalysisCandidate(null);
                    setAnalysisDetail(null);
                  }}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs rounded-xl border border-slate-700 transition"
                >
                  Close Analysis
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* PHASE 6 — SIDE-BY-SIDE CANDIDATE COMPARISON MODAL */}
        {/* ============================================================ */}
        {showComparisonModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-[#111a2c] border border-slate-700 rounded-2xl w-full max-w-7xl max-h-[92vh] flex flex-col overflow-hidden shadow-2xl">
              {/* Header */}
              <div className="p-5 border-b border-slate-800 bg-[#0b1425] flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    <Users size={18} className="text-purple-400" /> Side-by-Side Candidate Comparison
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Job: <span className="text-sky-300 font-semibold">{selectedJob?.title}</span> &bull; Comparing{" "}
                    <span className="text-purple-300 font-bold">{comparisonSelectedIds.length} candidate(s)</span>
                  </p>
                </div>
                <button
                  onClick={() => setShowComparisonModal(false)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold rounded-xl border border-slate-700 transition"
                >
                  ✕ Close Comparison
                </button>
              </div>

              {/* Body Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                {comparisonLoading ? (
                  <div className="h-64 flex flex-col items-center justify-center space-y-3">
                    <div className="w-8 h-8 border-3 border-purple-400 border-t-transparent rounded-full animate-spin" />
                    <p className="text-xs font-bold text-slate-300">Loading Candidate Intelligence for Comparison...</p>
                  </div>
                ) : (
                  <>
                    {/* SIDE-BY-SIDE CANDIDATE CARDS GRID */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {comparisonSelectedIds.map((appId) => {
                        const app = (isRanked && rankedResults.length > 0 ? rankedResults : applicants).find(
                          (a) => a.id === appId
                        );
                        if (!app) return null;

                        const intel = comparisonCandidateDetails[app.candidate_id];
                        const rankedApp = rankedResults.find((r) => r.id === appId);

                        return (
                          <div
                            key={appId}
                            className="bg-[#0b1425] border border-purple-500/30 rounded-2xl p-5 space-y-4 shadow-lg flex flex-col justify-between"
                          >
                            <div className="space-y-3">
                              {/* Header & Status */}
                              <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-3">
                                <div>
                                  <h3 className="font-bold text-white text-sm">{app.candidate_name}</h3>
                                  <p className="text-xs text-sky-400 font-medium">{app.headline}</p>
                                </div>
                                <select
                                  value={app.status}
                                  onChange={(e) => handleStatusUpdate(app.id, e.target.value)}
                                  className="px-2 py-1 rounded text-xs font-bold bg-[#111a2c] text-sky-300 border border-sky-500/30 outline-none cursor-pointer"
                                >
                                  <option value="SUBMITTED" className="bg-[#0b1425] text-white">SUBMITTED</option>
                                  <option value="REVIEWED" className="bg-[#0b1425] text-white">REVIEWED</option>
                                  <option value="SHORTLISTED" className="bg-[#0b1425] text-white">SHORTLISTED</option>
                                  <option value="INTERVIEW" className="bg-[#0b1425] text-white">INTERVIEW</option>
                                  <option value="SELECTED" className="bg-[#0b1425] text-white">SELECTED</option>
                                  <option value="REJECTED" className="bg-[#0b1425] text-white">REJECTED</option>
                                </select>
                              </div>

                              {/* Master Match Score (Phase 3/4 Score Reused) */}
                              <div className="bg-[#111a2c] p-3 rounded-xl border border-slate-800 flex items-center justify-between">
                                <div>
                                  <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-medium">Match Score</span>
                                  <span className="text-xl font-extrabold text-amber-400">
                                    {rankedApp ? `${rankedApp.score} / 100` : "Not Ranked"}
                                  </span>
                                </div>
                                {rankedApp && (
                                  <div className="text-right space-y-0.5">
                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 block">
                                      ✓ {rankedApp.eligibility_status}
                                    </span>
                                    <span className="text-[10px] text-slate-400 block font-mono">
                                      {rankedApp.confidence_tier}
                                    </span>
                                  </div>
                                )}
                              </div>

                              {/* Target Roles */}
                              {intel?.target_roles && intel.target_roles.length > 0 && (
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Target Roles:</span>
                                  <div className="flex flex-wrap gap-1">
                                    {intel.target_roles.map((r, idx) => (
                                      <span key={idx} className="px-2 py-0.5 text-[10px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-full">
                                        {r}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Candidate Skills with Provenance */}
                              <div className="space-y-1.5">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                  Provenanced Skills ({intel?.skills?.length || app.skills.length}):
                                </span>
                                <div className="flex flex-wrap gap-1 max-h-28 overflow-y-auto custom-scrollbar">
                                  {intel?.skills && intel.skills.length > 0
                                    ? intel.skills.map((s, idx) => (
                                        <span
                                          key={idx}
                                          className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                                            s.source === "both"
                                              ? "bg-purple-500/10 text-purple-300 border-purple-500/30"
                                              : s.source === "resume"
                                              ? "bg-blue-500/10 text-blue-300 border-blue-500/30"
                                              : "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                                          }`}
                                        >
                                          {s.name}
                                        </span>
                                      ))
                                    : app.skills.map((s, idx) => (
                                        <span key={idx} className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-[10px]">
                                          {s}
                                        </span>
                                      ))}
                                </div>
                              </div>

                              {/* Work Experience */}
                              <div className="space-y-1">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Experience:</span>
                                {intel?.experience && intel.experience.length > 0 ? (
                                  <div className="space-y-1 text-xs text-slate-300">
                                    {intel.experience.map((e, idx) => (
                                      <div key={idx} className="bg-[#111a2c] p-2 rounded-lg border border-slate-800">
                                        <div className="font-bold text-white">{e.role || "Role"}</div>
                                        <div className="text-[11px] text-slate-400">{e.company} ({e.duration || "N/A"})</div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <p className="text-xs text-slate-500 italic">No experience records found</p>
                                )}
                              </div>

                              {/* Education & Projects */}
                              <div className="grid grid-cols-2 gap-2 text-[11px]">
                                <div className="bg-[#111a2c] p-2 rounded-lg border border-slate-800">
                                  <span className="font-bold text-slate-400 block text-[10px] uppercase">Education</span>
                                  <span className="text-slate-200 font-semibold">
                                    {intel?.education && intel.education.length > 0 ? intel.education[0].degree || intel.education[0].institution : "Not listed"}
                                  </span>
                                </div>
                                <div className="bg-[#111a2c] p-2 rounded-lg border border-slate-800">
                                  <span className="font-bold text-slate-400 block text-[10px] uppercase">Projects</span>
                                  <span className="text-slate-200 font-semibold">
                                    {intel?.projects && intel.projects.length > 0 ? `${intel.projects.length} Project(s)` : "None listed"}
                                  </span>
                                </div>
                              </div>
                            </div>

                            {/* Card Footer Actions */}
                            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-semibold">
                              <button
                                onClick={() => handleViewResumeFromComparison(app.id)}
                                className="text-emerald-400 hover:underline flex items-center gap-1 cursor-pointer bg-transparent border-none p-0 text-xs font-semibold"
                              >
                                <FileText size={12} /> Resume PDF
                              </button>
                              <Link
                                href={`/recruiter/jobs/${selectedJobId}/applications/${app.id}`}
                                className="text-sky-400 hover:underline flex items-center gap-0.5"
                              >
                                Inspect Full Detail &rarr;
                              </Link>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* REQUIREMENT COMPARISON EVALUATION MATRIX */}
                    <div className="bg-[#0b1425] border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
                      <h3 className="font-bold text-white text-sm flex items-center gap-2">
                        <CheckCircle2 size={16} className="text-emerald-400" /> Evidence-Based Requirement Matrix
                      </h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                              <th className="p-3 bg-[#111a2c] rounded-l-lg">Job Requirement</th>
                              <th className="p-3 bg-[#111a2c]">Requirement Level</th>
                              {comparisonSelectedIds.map((appId) => {
                                const app = (isRanked && rankedResults.length > 0 ? rankedResults : applicants).find((a) => a.id === appId);
                                return (
                                  <th key={appId} className="p-3 bg-[#111a2c] font-bold text-white">
                                    {app?.candidate_name || appId}
                                  </th>
                                );
                              })}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60">
                            {intelligence?.extracted_data?.required_skills?.map((req, idx) => (
                              <tr key={`req-${idx}`} className="hover:bg-slate-900/30">
                                <td className="p-3 font-bold text-white">{req}</td>
                                <td className="p-3">
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20">
                                    REQUIRED
                                  </span>
                                </td>
                                {comparisonSelectedIds.map((appId) => {
                                  const app = rankedResults.find((r) => r.id === appId);
                                  const isMatched = app?.matched_skills?.some((s) => s.toLowerCase() === req.toLowerCase() || s.includes(req));
                                  return (
                                    <td key={appId} className="p-3">
                                      {isMatched ? (
                                        <span className="text-emerald-400 font-bold flex items-center gap-1">
                                          ✓ MATCHED
                                        </span>
                                      ) : (
                                        <span className="text-slate-500 font-medium">✗ NOT FOUND</span>
                                      )}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                            {intelligence?.extracted_data?.preferred_skills?.map((pref, idx) => (
                              <tr key={`pref-${idx}`} className="hover:bg-slate-900/30">
                                <td className="p-3 font-bold text-white">{pref}</td>
                                <td className="p-3">
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/10 text-sky-300 border border-sky-500/20">
                                    PREFERRED
                                  </span>
                                </td>
                                {comparisonSelectedIds.map((appId) => {
                                  const app = rankedResults.find((r) => r.id === appId);
                                  const isMatched = app?.matched_skills?.some((s) => s.toLowerCase() === pref.toLowerCase() || s.includes(pref));
                                  return (
                                    <td key={appId} className="p-3">
                                      {isMatched ? (
                                        <span className="text-emerald-400 font-bold flex items-center gap-1">
                                          ✓ MATCHED
                                        </span>
                                      ) : (
                                        <span className="text-slate-500 font-medium">✗ NOT FOUND</span>
                                      )}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
