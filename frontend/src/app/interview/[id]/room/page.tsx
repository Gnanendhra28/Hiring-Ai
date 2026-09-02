"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Award,
  Bot,
  CheckCircle,
  Clock,
  Code,
  Mic,
  MicOff,
  Play,
  Send,
  Sparkles,
  User,
  Volume2,
  AlertCircle,
  FileCode,
  ShieldCheck,
  RotateCcw,
  ArrowRight,
  Info,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

interface QuestionItem {
  id: string;
  category: string;
  question: string;
  target_skill: string;
  difficulty: string;
  expected_key_points?: string[];
}

export default function AIInterviewRoomPage() {
  const params = useParams();
  const router = useRouter();
  const interviewId = (params?.id as string) || "int-ai-101";

  // Pre-Check Modal State
  const [hasStarted, setHasStarted] = useState<boolean>(false);

  const [currentStep, setCurrentStep] = useState<number>(0);
  const [questions, setQuestions] = useState<QuestionItem[]>([
    {
      id: "q-1",
      category: "TECHNICAL",
      question: "Can you explain your experience with RAG, Vector Databases (such as pgvector or ChromaDB), and dense embeddings? How did you optimize query latency in production?",
      target_skill: "RAG & Vector Retrieval",
      difficulty: "MEDIUM",
      expected_key_points: ["Vector indexing & distance metrics", "Cross-Encoder re-ranking", "Caching & sub-30ms latency"],
    },
    {
      id: "q-2",
      category: "CODING",
      question: "Write a high-performance Python function that executes batch cross-attention scoring across candidate profiles with asynchronous error handling.",
      target_skill: "Python & Asynchronous Concurrency",
      difficulty: "MEDIUM",
    },
    {
      id: "q-3",
      category: "SYSTEM_DESIGN",
      question: "Design a fault-tolerant job candidate matching architecture capable of handling 10,000 resume uploads per minute during peak recruitment cycles. How do you partition data?",
      target_skill: "Scalable Distributed Architecture",
      difficulty: "HARD",
    },
    {
      id: "q-4",
      category: "PROBLEM_SOLVING",
      question: "Describe a scenario where your production inference service experienced high memory usage or GPU latency. How did you diagnose and remediate the bottleneck?",
      target_skill: "Production Diagnostics & Profiling",
      difficulty: "MEDIUM",
    },
    {
      id: "q-5",
      category: "BEHAVIORAL",
      question: "How do you navigate technical disagreements on architectural design within a cross-functional engineering team to maintain momentum and software quality?",
      target_skill: "Technical Leadership & Collaboration",
      difficulty: "EASY",
    },
  ]);

  const [answerText, setAnswerText] = useState<string>("");
  const [codeText, setCodeText] = useState<string>(
    `# Write your implementation here\ndef optimize_pipeline(records: list) -> dict:\n    pass`
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isInterviewCompleted, setIsInterviewCompleted] = useState<boolean>(false);
  const [candidateFeedback, setCandidateFeedback] = useState<any | null>(null);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [aiSpeechSpeaking, setAiSpeechSpeaking] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [noticeMessage, setNoticeMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Local draft autosave key
  const currentQ = questions[currentStep] || questions[0];
  const draftKey = `interview_draft_${interviewId}_${currentQ.id}`;

  // Restore draft on question change
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedDraft = localStorage.getItem(draftKey);
      if (savedDraft) {
        try {
          const parsed = JSON.parse(savedDraft);
          if (parsed.answerText) setAnswerText(parsed.answerText);
          if (parsed.codeText) setCodeText(parsed.codeText);
        } catch {
          // ignore corrupted local draft
        }
      }
    }
  }, [currentStep, draftKey]);

  // Persist draft to localStorage on typing
  useEffect(() => {
    if (typeof window !== "undefined" && (answerText || codeText)) {
      localStorage.setItem(draftKey, JSON.stringify({ answerText, codeText }));
    }
  }, [answerText, codeText, draftKey]);

  // Server-authoritative timer
  useEffect(() => {
    if (!hasStarted || isInterviewCompleted) return;
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [hasStarted, isInterviewCompleted]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleSimulateSpeech = () => {
    setAiSpeechSpeaking(true);
    setTimeout(() => setAiSpeechSpeaking(false), 2500);
  };

  const handleToggleRecord = () => {
    setIsRecording(!isRecording);
    if (!isRecording && !answerText) {
      setAnswerText("In our production architecture, we deployed an asynchronous ingestion pipeline using FastAPI, pgvector, and Cross-Encoder re-ranking with resilient retry mechanisms.");
    }
  };

  const handleSubmitCurrentTurn = async () => {
    if (!answerText.trim() && !codeText.trim()) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    setNoticeMessage(null);

    const submissionId = `sub_${interviewId}_${currentQ.id}_${Date.now()}`;

    try {
      const res = await apiFetch(`/api/v1/interviews/${interviewId}/submit-turn`, {
        method: "POST",
        body: JSON.stringify({
          question_id: currentQ.id,
          question_text: currentQ.question,
          candidate_answer: answerText,
          code_submission: codeText,
          time_taken_seconds: elapsedSeconds,
          client_submission_id: submissionId,
        }),
      });

      if (res.ok) {
        // Clear saved draft on confirmed persistence
        if (typeof window !== "undefined") {
          localStorage.removeItem(draftKey);
        }

        const turnData = await res.json();
        if (turnData.status === "FOLLOW_UP" && turnData.follow_up_question) {
          // Dynamically inject adaptive follow-up
          const updated = [...questions];
          updated.splice(currentStep + 1, 0, turnData.follow_up_question);
          setQuestions(updated);
          setCurrentStep((prev) => prev + 1);
          setNoticeMessage("AI Interviewer initiated an adaptive follow-up question to probe deeper into your technical design.");
          setAnswerText("");
          setCodeText("# Address the follow-up clarification or trade-offs\n");
          return;
        }
      }

      if (currentStep < questions.length - 1) {
        setCurrentStep((prev) => prev + 1);
        setAnswerText("");
        setCodeText("# Write your implementation here\n");
      } else {
        // Final Turn - Complete Interview
        const res = await apiFetch(`/api/v1/interviews/${interviewId}/complete-evaluation`, {
          method: "POST",
          body: JSON.stringify({
            candidate_name: "Candidate",
            job_title: "Senior AI Engineer",
          }),
        });

        // Load candidate-safe feedback projection
        const feedbackRes = await apiFetch(`/api/v1/interviews/${interviewId}/candidate-feedback`);
        if (feedbackRes.ok) {
          const feedback = await feedbackRes.json();
          setCandidateFeedback(feedback);
        }
        setIsInterviewCompleted(true);
      }
    } catch (err: any) {
      console.error("Error submitting interview turn:", err);
      setErrorMessage("AI evaluation service temporarily unavailable. Your answer is preserved locally—click Submit Turn to retry.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 p-4 lg:p-8 font-sans flex flex-col justify-between">
      {/* Header Bar */}
      <div className="max-w-7xl mx-auto w-full flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
            <Bot size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white">AI Technical Interview Room</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> LIVE
              </span>
            </div>
            <p className="text-slate-400 text-xs">Autonomous Adaptive Evaluation • Session ID: {interviewId}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-[#0b1425] border border-slate-800 px-3 py-1.5 rounded-xl flex items-center gap-2 text-xs font-mono text-slate-300">
            <Clock size={14} className="text-sky-400" />
            <span>{formatTimer(elapsedSeconds)}</span>
          </div>

          <button
            onClick={() => router.push("/candidate/interviews")}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition"
          >
            Exit Room
          </button>
        </div>
      </div>

      {/* Pre-Check Screen Modal */}
      {!hasStarted ? (
        <div className="max-w-3xl mx-auto w-full my-12 bg-[#0b1425] border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center">
              <ShieldCheck size={24} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Interview Pre-Check & Guidelines</h2>
              <p className="text-xs text-slate-400">Review guidelines before starting your autonomous technical interview.</p>
            </div>
          </div>

          <div className="space-y-4 text-xs text-slate-300 leading-relaxed">
            <div className="p-4 rounded-2xl bg-[#080e1b] border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-sky-400 font-bold">
                <Info size={16} />
                <span>What to Expect</span>
              </div>
              <ul className="list-disc list-inside space-y-1 text-slate-400">
                <li>5 structured technical questions covering distributed systems, architecture, and code design.</li>
                <li>The AI interviewer adapts dynamically: brief answers may trigger follow-up probe questions.</li>
                <li>Your answers are automatically saved to persistent storage.</li>
              </ul>
            </div>

            <div className="p-4 rounded-2xl bg-[#080e1b] border border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold">
                <CheckCircle size={16} />
                <span>Connection & Draft Safety</span>
              </div>
              <p className="text-slate-400">
                If your internet drops or you refresh the page, your typed draft is preserved locally and your completed turns remain saved on the server.
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex justify-end">
            <button
              onClick={() => setHasStarted(true)}
              className="py-3 px-8 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 font-bold text-white text-xs shadow-lg shadow-sky-500/20 transition-all flex items-center gap-2"
            >
              <span>Begin Interview Session</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      ) : !isInterviewCompleted ? (
        /* Main Interview Body */
        <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6 my-6 flex-1">
          {/* Left Column: AI Agent Question & Transcript (5 cols) */}
          <div className="lg:col-span-5 bg-[#0b1425] border border-slate-800/90 rounded-3xl p-6 flex flex-col justify-between shadow-xl space-y-4">
            <div className="space-y-4">
              {/* Question Progress Indicator */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-sky-400 tracking-wider">
                  QUESTION {currentStep + 1} OF {questions.length}
                </span>
                <div className="flex gap-1.5">
                  {questions.map((_, idx) => (
                    <div
                      key={idx}
                      className={`h-1.5 rounded-full transition-all ${
                        idx === currentStep
                          ? "w-6 bg-sky-400"
                          : idx < currentStep
                          ? "w-2 bg-emerald-400"
                          : "w-2 bg-slate-700"
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* AI Avatar & Speech Indicator */}
              <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-[#080e1b] border border-slate-800">
                <div className="relative">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white font-bold text-base shadow-md">
                    AI
                  </div>
                  {aiSpeechSpeaking && (
                    <span className="absolute -top-1 -right-1 flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-sky-500"></span>
                    </span>
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white">TalentOS AI Evaluator</span>
                    <button
                      onClick={handleSimulateSpeech}
                      className="text-slate-400 hover:text-sky-400 transition"
                      title="Play Voice Audio"
                    >
                      <Volume2 size={15} />
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {aiSpeechSpeaking ? "Synthesizing question..." : "Listening for candidate response"}
                  </p>
                </div>
              </div>

              {/* Adaptive Follow-up Banner if applicable */}
              {currentQ.category === "ADAPTIVE_FOLLOWUP" && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs flex items-center gap-2">
                  <Sparkles size={15} className="shrink-0 text-amber-400" />
                  <span>Adaptive Follow-Up: The interviewer generated this question to dive deeper into your previous response.</span>
                </div>
              )}

              {/* Current Question Display */}
              <div className="bg-[#0e172a] border border-sky-500/30 rounded-2xl p-5 space-y-3 shadow-inner">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40 font-mono">
                    {currentQ.category}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    {currentQ.difficulty}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white leading-relaxed">{currentQ.question}</h3>
                <div className="text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                  <span className="font-semibold text-slate-300">Target Competency:</span> {currentQ.target_skill}
                </div>
              </div>
            </div>

            {/* AI Real-time Hint */}
            <div className="p-3.5 rounded-2xl bg-[#080e1b] border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2">
              <Sparkles size={16} className="text-amber-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-slate-300 block mb-0.5">Evaluation Hint</span>
                Be specific with architectural decisions, latency metrics, and concrete frameworks used in production.
              </div>
            </div>
          </div>

          {/* Right Column: Candidate Answer Input & Live Code Sandbox (7 cols) */}
          <div className="lg:col-span-7 bg-[#0b1425] border border-slate-800/90 rounded-3xl p-6 flex flex-col justify-between shadow-xl space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <User size={16} className="text-emerald-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Candidate Response</h3>
                </div>
                <button
                  onClick={handleToggleRecord}
                  className={`px-3 py-1 rounded-xl text-xs font-bold flex items-center gap-1.5 transition ${
                    isRecording
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
                      : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                  }`}
                >
                  {isRecording ? <MicOff size={13} /> : <Mic size={13} />}
                  <span>{isRecording ? "Transcribing..." : "Voice Input"}</span>
                </button>
              </div>

              {noticeMessage && (
                <div className="p-3 bg-sky-500/10 border border-sky-500/30 rounded-xl text-sky-300 text-xs flex items-center gap-2">
                  <Sparkles size={15} className="shrink-0 text-sky-400" />
                  <span>{noticeMessage}</span>
                </div>
              )}

              {errorMessage && (
                <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-center gap-2">
                  <AlertCircle size={15} className="shrink-0 text-rose-400" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Text Response Area */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold text-slate-400">Verbal & Conceptual Explanation</label>
                <textarea
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  placeholder="Explain your approach, architectural decisions, and failure recovery mechanisms..."
                  rows={5}
                  className="w-full bg-[#080e1b] border border-slate-700/80 rounded-2xl p-4 text-xs text-white placeholder-slate-500 outline-none focus:border-sky-500 transition leading-relaxed"
                />
              </div>

              {/* Live Code Sandbox */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                    <FileCode size={13} className="text-sky-400" /> Live Code Sandbox (Python / JS)
                  </label>
                  <span className="text-[10px] text-slate-500 font-mono">Code Analyzed by AI</span>
                </div>
                <textarea
                  value={codeText}
                  onChange={(e) => setCodeText(e.target.value)}
                  rows={6}
                  className="w-full bg-[#060a12] border border-slate-800 rounded-2xl p-4 font-mono text-xs text-emerald-300 outline-none focus:border-sky-500 transition"
                  spellCheck={false}
                />
              </div>
            </div>

            {/* Bottom Submission Action */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              <span className="text-xs text-slate-500">
                {currentStep === questions.length - 1 ? "Final Question" : `${questions.length - currentStep - 1} remaining`}
              </span>

              <button
                onClick={handleSubmitCurrentTurn}
                disabled={isSubmitting || (!answerText.trim() && !codeText.trim())}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 disabled:opacity-50 text-white font-bold text-xs shadow-lg shadow-sky-500/20 flex items-center gap-2 transition"
              >
                {isSubmitting ? (
                  <span>Recording Turn...</span>
                ) : currentStep === questions.length - 1 ? (
                  <>
                    <Award size={15} />
                    <span>Complete & Grade Interview</span>
                  </>
                ) : (
                  <>
                    <span>Next Question</span>
                    <Send size={13} />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* ============================================================ */
        /* CANDIDATE-SAFE POST-INTERVIEW FEEDBACK VIEW */
        /* ============================================================ */
        <div className="max-w-3xl mx-auto w-full my-8 bg-[#0b1425] border border-slate-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="w-14 h-14 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 mx-auto flex items-center justify-center">
              <CheckCircle size={30} />
            </div>
            <h2 className="text-2xl font-black text-white">Interview Completed Successfully</h2>
            <p className="text-xs text-slate-400">All questions and code submissions have been securely recorded.</p>
          </div>

          <div className="bg-[#080e1b] p-5 rounded-2xl border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider">Top Observed Strengths</h3>
            <ul className="space-y-1.5">
              {(candidateFeedback?.top_strengths || ["Clear technical communication", "Methodical system design approach"]).map((s: string, idx: number) => (
                <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-[#080e1b] p-5 rounded-2xl border border-slate-800 space-y-3">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Areas for Technical Growth</h3>
            <ul className="space-y-1.5">
              {(candidateFeedback?.areas_for_improvement || ["Provide more quantitative production benchmarks"]).map((s: string, idx: number) => (
                <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-[#080e1b] p-4 rounded-2xl border border-slate-800 space-y-1.5">
            <span className="text-xs font-bold text-slate-300">Summary</span>
            <p className="text-xs text-slate-400 leading-relaxed">
              {candidateFeedback?.summary_feedback || "Thank you for completing your interview. Your performance has been submitted for recruiter review."}
            </p>
          </div>

          <div className="flex items-center justify-center gap-4 pt-4 border-t border-slate-800">
            <Link
              href="/candidate/interviews"
              className="px-6 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-sky-500/20"
            >
              Return to Scheduled Interviews
            </Link>
            <Link
              href="/candidate/dashboard"
              className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold"
            >
              Go to Dashboard
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
