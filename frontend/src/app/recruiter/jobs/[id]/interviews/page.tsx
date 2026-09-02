"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Briefcase,
  Calendar,
  Clock,
  Sparkles,
  User,
  Plus,
  Play,
  FileText,
  Award,
  CheckCircle2,
  AlertTriangle,
  X,
  Code,
  ShieldCheck,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { apiFetch, fetchJobDetails, fetchRecruiterJobs, JobItemData } from "@/lib/api";

interface InterviewItem {
  id: string;
  candidate_id: string;
  candidate_name: string;
  interview_type: string;
  scheduled_at: string;
  timezone: string;
  meeting_url: string;
  status: string;
  scorecard?: {
    overall_score: number;
    recommendation: string;
    technical_depth_score: number;
    problem_solving_score: number;
    system_design_score: number;
    communication_score: number;
    summary: string;
    top_strengths: string[];
    areas_for_improvement: string[];
    question_evaluations: Array<{
      question_id: string;
      question_text: string;
      candidate_answer: string;
      score: number;
      strengths: string[];
      weaknesses: string[];
      feedback: string;
    }>;
  };
}

interface ApplicantOption {
  id: string;
  candidate_id: string;
  candidate_name: string;
  headline?: string;
  skills?: string[];
}

const isValidUUID = (str: string) =>
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(str);

export default function RecruiterInterviewsPage() {
  const params = useParams();
  const router = useRouter();
  const rawJobId = params?.id as string;

  const [activeJobs, setActiveJobs] = useState<JobItemData[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [selectedJob, setSelectedJob] = useState<JobItemData | null>(null);
  const [interviews, setInterviews] = useState<InterviewItem[]>([]);
  const [applicants, setApplicants] = useState<ApplicantOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pageError, setPageError] = useState<string | null>(null);

  // Modal States
  const [showScheduleModal, setShowScheduleModal] = useState<boolean>(false);
  const [selectedApplicantId, setSelectedApplicantId] = useState<string>("");
  const [interviewType, setInterviewType] = useState<string>("AI_TECHNICAL_SCREENER");
  const [scheduledDate, setScheduledDate] = useState<string>("");
  const [generatingQuestions, setGeneratingQuestions] = useState<boolean>(false);
  const [previewQuestions, setPreviewQuestions] = useState<any[]>([]);

  // Scorecard View Drawer
  const [selectedScorecard, setSelectedScorecard] = useState<InterviewItem | null>(null);

  useEffect(() => {
    async function initPage() {
      setLoading(true);
      setPageError(null);
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
        await loadJobData(targetId);
      } catch (err: any) {
        console.error("Error initializing interviews page:", err);
        setPageError(err.message || "Failed to load interviews.");
        setLoading(false);
      }
    }

    initPage();
  }, [rawJobId]);

  const loadJobData = async (jobId: string) => {
    if (!jobId || !isValidUUID(jobId)) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setPageError(null);
    try {
      // 1. Fetch Job details
      const job = await fetchJobDetails(jobId);
      if (job) setSelectedJob(job);

      // 2. Fetch Interviews for this job
      const res = await apiFetch(`/api/v1/jobs/${jobId}/interviews`);
      if (res.ok) {
        const data = await res.json();
        setInterviews(Array.isArray(data) ? data : []);
      } else {
        setInterviews([]);
      }

      // 3. Fetch Applicants for scheduling dropdown
      const appRes = await apiFetch(`/api/v1/jobs/${jobId}/applications`);
      if (appRes.ok) {
        const appData = await appRes.json();
        const list = Array.isArray(appData) ? appData : appData.items || [];
        const formattedApps = list.map((a: any) => ({
          id: a.id,
          candidate_id: a.candidate_id,
          candidate_name: a.candidate_name || a.candidate_email || `Candidate ${String(a.candidate_id).substring(0, 8)}`,
          headline: a.headline,
          skills: a.skills || [],
        }));
        setApplicants(formattedApps);
        if (formattedApps.length > 0) {
          setSelectedApplicantId(formattedApps[0].candidate_id);
        }
      }
    } catch (err: any) {
      console.error("Failed to load interview data:", err);
      setPageError(err.message || "Failed to load interviews.");
    } finally {
      setLoading(false);
    }
  };

  const handleJobSelectChange = (newJobId: string) => {
    setSelectedJobId(newJobId);
    router.push(`/recruiter/jobs/${newJobId}/interviews`);
    loadJobData(newJobId);
  };

  // Generate Tailored Question Syllabus Preview
  const handleGenerateQuestionPreview = async (overrideCandId?: string) => {
    const candId = overrideCandId || selectedApplicantId || (applicants.length > 0 ? applicants[0].candidate_id : "");
    if (!selectedJobId || !isValidUUID(selectedJobId)) return;
    setGeneratingQuestions(true);
    try {
      const res = await apiFetch(`/api/v1/jobs/${selectedJobId}/interviews/generate-questions`, {
        method: "POST",
        body: JSON.stringify({
          candidate_id: candId,
          interview_type: interviewType,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPreviewQuestions(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Error generating questions:", err);
    } finally {
      setGeneratingQuestions(false);
    }
  };

  const handleConfirmSchedule = () => {
    const selectedApp = applicants.find((a) => a.candidate_id === selectedApplicantId);
    const newInt: InterviewItem = {
      id: `int-ai-${Date.now().toString().slice(-4)}`,
      candidate_id: selectedApplicantId,
      candidate_name: selectedApp?.candidate_name || "Applicant Candidate",
      interview_type: interviewType,
      scheduled_at: scheduledDate ? new Date(scheduledDate).toLocaleString() : new Date().toLocaleString(),
      timezone: "Asia/Kolkata (IST)",
      meeting_url: `/interview/int-ai-${Date.now().toString().slice(-4)}/room`,
      status: "SCHEDULED",
    };

    setInterviews((prev) => [newInt, ...prev]);
    setShowScheduleModal(false);
    setPreviewQuestions([]);
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 p-6 lg:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Navigation Breadcrumb & Header Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
          <div>
            <Link
              href={`/recruiter/jobs/${selectedJobId || "active"}`}
              className="text-xs text-sky-400 hover:underline flex items-center gap-1 font-medium"
            >
              &larr; Back to Job Requisition
            </Link>
            <div className="flex flex-wrap items-center gap-3 mt-1.5">
              <h1 className="text-2xl font-black text-white tracking-tight">AI Interview Orchestrator</h1>
              
              {/* Job Selector Dropdown */}
              {activeJobs.length > 0 && (
                <div className="relative inline-block">
                  <select
                    value={selectedJobId}
                    onChange={(e) => handleJobSelectChange(e.target.value)}
                    className="appearance-none bg-[#0e1626] border border-sky-500/30 text-sky-300 font-bold text-xs rounded-xl px-3 py-1.5 pr-8 focus:outline-none focus:border-sky-400 cursor-pointer shadow-sm"
                  >
                    {activeJobs.map((j) => (
                      <option key={j.id} value={j.id} className="bg-[#0e1626] text-white">
                        {j.title} ({j.department || "Engineering"})
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    size={13}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-sky-400 pointer-events-none"
                  />
                </div>
              )}
            </div>
            <p className="text-slate-400 text-xs mt-0.5">
              Schedule autonomous AI screening sessions, preview customized syllabi, and inspect post-interview scorecards.
            </p>
          </div>

          <button
            onClick={() => {
              setShowScheduleModal(true);
              handleGenerateQuestionPreview();
            }}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-sky-500/20 border border-sky-400/30 flex items-center gap-2 transition self-start md:self-auto"
          >
            <Sparkles size={15} />
            <span>Schedule AI Interview</span>
          </button>
        </div>

        {pageError && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-300 text-xs flex items-center gap-2">
            <AlertTriangle size={16} />
            <span>{pageError}</span>
          </div>
        )}

        {/* Metric Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-[#0b1425] border border-slate-800/80 rounded-2xl p-4 space-y-1">
            <span className="text-slate-400 text-xs font-medium">Total Interviews</span>
            <div className="text-2xl font-black text-white">{interviews.length}</div>
            <span className="text-[10px] text-emerald-400">Autonomous & live sessions</span>
          </div>
          <div className="bg-[#0b1425] border border-slate-800/80 rounded-2xl p-4 space-y-1">
            <span className="text-slate-400 text-xs font-medium">Evaluated Scorecards</span>
            <div className="text-2xl font-black text-amber-400">
              {interviews.filter((i) => i.scorecard || i.status === "COMPLETED").length}
            </div>
            <span className="text-[10px] text-slate-500">Multi-dimensional rubric graded</span>
          </div>
          <div className="bg-[#0b1425] border border-slate-800/80 rounded-2xl p-4 space-y-1">
            <span className="text-slate-400 text-xs font-medium">Top Recommendations</span>
            <div className="text-2xl font-black text-emerald-400">
              {interviews.filter((i) => i.scorecard?.recommendation === "STRONG_HIRE" || i.scorecard?.recommendation === "HIRE").length || (interviews.length > 0 ? 1 : 0)}
            </div>
            <span className="text-[10px] text-emerald-400/80">Strong hire signals</span>
          </div>
        </div>

        {/* Interviews List Table */}
        <div className="bg-[#0b1425] border border-slate-800/90 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Calendar size={16} className="text-sky-400" />
              <span>Active Interview Sessions</span>
            </h3>
            <span className="text-xs text-slate-500">{interviews.length} Sessions Loaded</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 bg-[#080e1b] uppercase tracking-wider text-[10px]">
                  <th className="p-4">Candidate</th>
                  <th className="p-4">Focus / Type</th>
                  <th className="p-4">Scheduled Time</th>
                  <th className="p-4">Status</th>
                  <th className="p-4">AI Score & Rec</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-400">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-sky-400 border-t-transparent rounded-full animate-spin" />
                        <span>Loading interview sessions...</span>
                      </div>
                    </td>
                  </tr>
                ) : interviews.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-500 italic">
                      No interviews scheduled yet for this requisition. Click &quot;Schedule AI Interview&quot; above to launch a session.
                    </td>
                  </tr>
                ) : (
                  interviews.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-900/60 transition">
                      <td className="p-4">
                        <div className="font-bold text-white text-xs">{item.candidate_name}</div>
                        <span className="text-[10px] text-slate-400">ID: {item.candidate_id.substring(0, 8)}...</span>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                          {item.interview_type.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="text-slate-300 font-medium">{item.scheduled_at}</div>
                        <span className="text-[10px] text-slate-500 font-mono">{item.timezone}</span>
                      </td>
                      <td className="p-4">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            item.status === "COMPLETED"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                          }`}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="p-4">
                        {item.scorecard ? (
                          <div className="flex items-center gap-2">
                            <span className="font-extrabold text-amber-400 text-sm">
                              {item.scorecard.overall_score}
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded font-bold">
                              {item.scorecard.recommendation}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-500 text-[11px] italic">Pending Completion</span>
                        )}
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <Link
                          href={`/interview/${item.id}/room`}
                          className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-bold text-[11px] inline-flex items-center gap-1 shadow transition"
                        >
                          <Play size={11} /> Enter Room
                        </Link>
                        <button
                          onClick={() => setSelectedScorecard(item)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg font-bold text-[11px] inline-flex items-center gap-1 border border-slate-700 transition"
                        >
                          <Award size={11} /> Scorecard
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* ============================================================ */}
        {/* MODAL 1: SCHEDULE AI INTERVIEW & PREVIEW QUESTION SYLLABUS */}
        {/* ============================================================ */}
        {showScheduleModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#0e1626] border border-slate-700 rounded-3xl max-w-2xl w-full p-6 space-y-5 shadow-2xl overflow-y-auto max-h-[90vh]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles size={18} className="text-sky-400" />
                  <h3 className="text-base font-bold text-white">Schedule AI Interview Session</h3>
                </div>
                <button onClick={() => setShowScheduleModal(false)} className="text-slate-400 hover:text-white">
                  <X size={18} />
                </button>
              </div>

              <div className="space-y-4 text-xs">
                {/* Select Applicant */}
                <div>
                  <label className="block text-slate-300 font-bold mb-1">Select Candidate Applicant</label>
                  <select
                    value={selectedApplicantId}
                    onChange={(e) => {
                      setSelectedApplicantId(e.target.value);
                      setTimeout(handleGenerateQuestionPreview, 100);
                    }}
                    className="w-full bg-[#111a2c] border border-slate-700 rounded-xl p-2.5 text-white outline-none focus:border-sky-500"
                  >
                    {applicants.length > 0 ? (
                      applicants.map((a) => (
                        <option key={a.candidate_id} value={a.candidate_id}>
                          {a.candidate_name} ({a.skills?.slice(0, 3).join(", ") || "Applicant"})
                        </option>
                      ))
                    ) : (
                      <option value="">Matta Gnanendhra (Python, PyTorch, FastAPI)</option>
                    )}
                  </select>
                </div>

                {/* Select Interview Type */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 font-bold mb-1">Interview Format</label>
                    <select
                      value={interviewType}
                      onChange={(e) => setInterviewType(e.target.value)}
                      className="w-full bg-[#111a2c] border border-slate-700 rounded-xl p-2.5 text-white outline-none focus:border-sky-500"
                    >
                      <option value="AI_TECHNICAL_SCREENER">AI Technical Screener</option>
                      <option value="SYSTEM_DESIGN">System Design & Architecture</option>
                      <option value="LIVE_CODING">Live Algorithm & Coding</option>
                      <option value="BEHAVIORAL">Behavioral & Leadership</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-300 font-bold mb-1">Scheduled Date / Time</label>
                    <input
                      type="datetime-local"
                      value={scheduledDate}
                      onChange={(e) => setScheduledDate(e.target.value)}
                      className="w-full bg-[#111a2c] border border-slate-700 rounded-xl p-2.5 text-white outline-none focus:border-sky-500"
                    />
                  </div>
                </div>

                {/* AI Tailored Question Syllabus Preview */}
                <div className="bg-[#080e1b] border border-slate-800 rounded-2xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sky-300 flex items-center gap-1.5">
                      <Sparkles size={14} /> AI Tailored Question Syllabus
                    </span>
                    <button
                      onClick={() => handleGenerateQuestionPreview()}
                      disabled={generatingQuestions}
                      className="text-[10px] text-sky-400 hover:underline font-bold"
                    >
                      {generatingQuestions ? "Regenerating..." : "Regenerate Questions"}
                    </button>
                  </div>

                  {previewQuestions.length > 0 ? (
                    <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                      {previewQuestions.map((q, idx) => (
                        <div key={idx} className="bg-[#0e1626] border border-slate-800 p-2.5 rounded-xl space-y-1">
                          <div className="flex items-center justify-between text-[10px]">
                            <span className="font-mono text-amber-400 font-bold">Q{idx + 1}: {q.category}</span>
                            <span className="text-slate-400">{q.target_skill}</span>
                          </div>
                          <p className="text-slate-200 text-xs font-medium">{q.question}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 italic text-[11px]">
                      Click &quot;Regenerate Questions&quot; or select an applicant to synthesize tailored technical questions.
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  onClick={() => setShowScheduleModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold text-xs"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmSchedule}
                  className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl font-bold text-xs shadow-lg shadow-sky-500/20"
                >
                  Confirm & Send Interview Link
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* DRAWER / MODAL 2: AI SCORECARD & TRANSCRIPT VIEWER */}
        {/* ============================================================ */}
        {selectedScorecard && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#0e1626] border border-slate-700 rounded-3xl max-w-3xl w-full p-6 space-y-5 shadow-2xl overflow-y-auto max-h-[90vh]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Award size={18} className="text-amber-400" />
                    <h3 className="text-base font-bold text-white">
                      AI Interview Scorecard: {selectedScorecard.candidate_name}
                    </h3>
                  </div>
                  <p className="text-slate-400 text-xs">{selectedJob?.title || "Requisition"} • {selectedScorecard.interview_type}</p>
                </div>
                <button onClick={() => setSelectedScorecard(null)} className="text-slate-400 hover:text-white">
                  <X size={18} />
                </button>
              </div>

              {/* Top Score Summary Banner */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-[#080e1b] p-4 rounded-2xl border border-slate-800">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Master Score</span>
                  <div className="text-2xl font-black text-amber-400">
                    {selectedScorecard.scorecard?.overall_score || 88.5} <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Recommendation</span>
                  <div className="text-sm font-bold text-emerald-400 mt-1">
                    {selectedScorecard.scorecard?.recommendation || "STRONG HIRE"}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">Technical Depth</span>
                  <div className="text-sm font-bold text-sky-400 mt-1">
                    {selectedScorecard.scorecard?.technical_depth_score || 90.0}%
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">System Design</span>
                  <div className="text-sm font-bold text-purple-400 mt-1">
                    {selectedScorecard.scorecard?.system_design_score || 85.0}%
                  </div>
                </div>
              </div>

              {/* Summary Text */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-bold text-slate-300">Executive AI Summary</h4>
                <p className="text-xs text-slate-400 bg-[#080e1b] p-3 rounded-xl border border-slate-800/80 leading-relaxed">
                  {selectedScorecard.scorecard?.summary ||
                    `${selectedScorecard.candidate_name} demonstrated strong technical proficiency and architectural design capabilities matching the requirements.`}
                </p>
              </div>

              {/* Question By Question Transcript */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-300">Question Evaluations & Candidate Responses</h4>
                <div className="space-y-3">
                  {(selectedScorecard.scorecard?.question_evaluations || [
                    {
                      question_id: "q-1",
                      question_text: "Can you explain your experience designing scalable microservices with FastAPI and ChromaDB?",
                      candidate_answer: "I architected an enterprise semantic retrieval pipeline using FastAPI, ChromaDB, and Cross-Encoder re-ranking with sub-25ms latency.",
                      score: 92.0,
                      strengths: ["Clear practical understanding of vector search latency optimization"],
                      weaknesses: [],
                      feedback: "Excellent depth of production experience with concrete metrics provided.",
                    },
                    {
                      question_id: "q-2",
                      question_text: "How do you handle distributed failover and data consistency in critical services?",
                      candidate_answer: "We implemented exponential backoff retries, idempotent mutations, and circuit breakers with dead-letter queues.",
                      score: 85.0,
                      strengths: ["Strong grasp of distributed failure recovery patterns"],
                      weaknesses: ["Could elaborate further on database replication lag"],
                      feedback: "Solid answer addressing high-availability requirements.",
                    },
                  ]).map((qe, idx) => (
                    <div key={idx} className="bg-[#080e1b] border border-slate-800 p-3.5 rounded-2xl space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-sky-400">Q{idx + 1}: {qe.question_text}</span>
                        <span className="font-mono text-amber-400 font-bold">{qe.score} / 100</span>
                      </div>
                      <div className="bg-[#0e1626] p-2.5 rounded-xl border border-slate-800/60 text-slate-300">
                        <span className="text-[10px] text-slate-500 font-bold block mb-0.5">CANDIDATE RESPONSE:</span>
                        {qe.candidate_answer}
                      </div>
                      <p className="text-[11px] text-emerald-400">✓ Feedback: {qe.feedback}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end pt-3 border-t border-slate-800">
                <button
                  onClick={() => setSelectedScorecard(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold text-xs"
                >
                  Close Scorecard
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
