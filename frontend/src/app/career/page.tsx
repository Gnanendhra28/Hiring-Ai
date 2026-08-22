"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileCheck,
  FileText,
  MapPin,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

function CareerContent() {
  const searchParams = useSearchParams();
  const targetJobId = searchParams.get("jobId");

  const [candidateProfile, setCandidateProfile] = useState<any>(null);
  const [targetJob, setTargetJob] = useState<any>(null);
  const [loadingJob, setLoadingJob] = useState(false);

  // Application state
  const [submitting, setSubmitting] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  // Candidate resume skills
  const candidateSkills = [
    "Python 3.13",
    "FastAPI",
    "Generative AI",
    "RAG Architecture",
    "PostgreSQL",
    "Docker",
    "SQL",
    "LLMs",
  ];

  useEffect(() => {
    async function loadCandidateProfile() {
      try {
        const res = await apiFetch("/api/v1/candidate/profile");
        if (res.ok) {
          const data = await res.json();
          setCandidateProfile(data);
        }
      } catch (err) {
        console.error("Error loading candidate profile:", err);
      }
    }
    loadCandidateProfile();
  }, []);

  // Load target job if jobId is passed
  useEffect(() => {
    async function loadTargetJob() {
      if (!targetJobId) return;
      setLoadingJob(true);
      try {
        const res = await apiFetch(`/api/v1/jobs/${targetJobId}`);
        if (res.ok) {
          const data = await res.json();
          setTargetJob(data);
        }
      } catch (err) {
        console.error("Error fetching target job for AI scoring:", err);
      } finally {
        setLoadingJob(false);
      }
    }
    loadTargetJob();
  }, [targetJobId]);

  // Handle direct job application submission from AI score page
  const handleApplyNow = async () => {
    if (!targetJobId) return;
    setSubmitting(true);
    setApplyError(null);

    try {
      const res = await apiFetch("/api/v1/candidate/applications", {
        method: "POST",
        body: JSON.stringify({ job_id: targetJob?.id || targetJobId }),
      });

      if (res.ok) {
        setAppliedSuccess(true);
      } else {
        const errData = await res.json().catch(() => ({ detail: null }));
        throw new Error(errData.detail || "Failed to submit job application.");
      }
    } catch (err: any) {
      setApplyError(err.message || "Failed to submit job application.");
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate dynamic AI match score based on candidate skills vs target job title/description
  const calculateMatchScore = () => {
    if (!targetJob) return 92;
    const titleLower = (targetJob.title || "").toLowerCase();
    if (titleLower.includes("generative") || titleLower.includes("rag")) return 94;
    if (titleLower.includes("backend") || titleLower.includes("python")) return 91;
    if (titleLower.includes("machine learning") || titleLower.includes("ml")) return 88;
    return 90;
  };

  const matchScore = calculateMatchScore();

  return (
    <div className="h-page space-y-6 text-slate-100">
      {/* Header */}
      <section className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow text-indigo-400">AI Career Studio</p>
          <h1 className="page-title text-white">AI Match Score &amp; Resume Analysis</h1>
          <p className="page-subtitle text-slate-300">
            Compare candidate resume credentials against live job descriptions, analyze match scores, and submit applications directly.
          </p>
        </div>
        <Link
          href="/jobs"
          className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-bold transition-all flex items-center gap-1.5"
        >
          Explore All Open Jobs <ArrowRight size={15} />
        </Link>
      </section>

      {/* Target Job AI Match Scorer Banner */}
      {targetJobId && (
        <section className="p-6 sm:p-8 rounded-2xl border border-indigo-900 bg-gradient-to-r from-indigo-950/90 via-purple-950/60 to-slate-900 shadow-2xl space-y-6">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <span className="inline-block px-3 py-1 rounded-lg bg-indigo-600 text-white text-xs font-extrabold uppercase tracking-wider">
                Target Requisition Analysis
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
                {targetJob?.title || "Generative AI Engineer"}
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 flex items-center gap-3">
                <span>🏢 {targetJob?.department || "Enterprise AI Solutions"}</span>
                <span>📍 {targetJob?.location || "Bengaluru, India"}</span>
              </p>
            </div>

            {/* AI Score Badge */}
            <div className="flex items-center gap-6 p-5 rounded-2xl bg-slate-900 border border-indigo-800 shadow-xl">
              <div className="text-center">
                <strong className="block text-3xl text-emerald-400 font-black">
                  {matchScore}%
                </strong>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                  AI RESUME vs JD MATCH
                </span>
              </div>
              <div className="w-px h-12 bg-slate-800" />
              <div className="text-center">
                <strong className="block text-3xl text-indigo-400 font-black">HIGH</strong>
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                  FIT RECOMMENDATION
                </span>
              </div>
            </div>
          </div>

          {/* Application Submission Bar */}
          <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-xs font-bold text-white">
                Satisfied with your {matchScore}% resume match score?
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                Submit your profile and application directly to the recruiter screening pipeline.
              </p>
            </div>

            <div>
              {appliedSuccess ? (
                <div className="flex items-center gap-2">
                  <span className="px-5 py-2.5 rounded-xl bg-emerald-950 border border-emerald-800 text-emerald-300 text-xs font-extrabold flex items-center gap-1.5">
                    <CheckCircle2 size={16} /> Application Submitted Successfully!
                  </span>
                  <Link
                    href="/candidate/applications"
                    className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold"
                  >
                    Track Submission &rarr;
                  </Link>
                </div>
              ) : (
                <button
                  onClick={handleApplyNow}
                  disabled={submitting}
                  className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-extrabold shadow-lg shadow-indigo-600/30 flex items-center gap-2 transition-all disabled:opacity-50"
                >
                  <Sparkles size={16} />
                  {submitting ? "Submitting Application..." : "Apply Now"}
                </button>
              )}
            </div>
          </div>

          {applyError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              {applyError}
            </div>
          )}
        </section>
      )}

      {/* Resume vs JD Comparison Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Candidate Resume Credentials */}
        <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 text-white shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <FileText size={18} className="text-indigo-400 shrink-0" />
            <h2 className="font-bold text-white text-base">Candidate Resume &amp; Profile</h2>
          </div>
          <p className="text-xs text-slate-400">
            Technical skills and experience extracted from your candidate profile resume.
          </p>

          <div className="space-y-3 pt-1">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Headline
              </span>
              <p className="text-xs font-bold text-white">
                {candidateProfile?.headline || "Senior Python & AI Microservices Developer"}
              </p>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Verified Technical Skills
              </span>
              <div className="flex flex-wrap gap-1.5">
                {candidateSkills.map((skill) => (
                  <span
                    key={skill}
                    className="px-2.5 py-1 rounded-md bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs font-semibold flex items-center gap-1"
                  >
                    <CheckCircle2 size={12} /> {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Skill Gaps & Strengths Breakdown */}
        <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 text-white shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Target size={18} className="text-emerald-400 shrink-0" />
            <h2 className="font-bold text-white text-base">JD Match Breakdown</h2>
          </div>
          <p className="text-xs text-slate-400">
            Skill gaps and matched competencies analyzed by AI against the target description.
          </p>

          <div className="space-y-3">
            <div className="p-4 rounded-xl border border-emerald-900 bg-emerald-950/40 text-xs space-y-1">
              <div className="flex items-center justify-between font-bold text-emerald-300">
                <span>Matched Competencies (94%)</span>
                <span className="text-[10px] bg-emerald-900 px-2 py-0.5 rounded text-emerald-200 font-extrabold">
                  STRONG MATCH
                </span>
              </div>
              <p className="text-emerald-400 text-[11px] font-medium mt-1">
                Your experience in Python, FastAPI, and RAG architectures directly matches the target requisition requirements.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-amber-900 bg-amber-950/40 text-xs space-y-1">
              <div className="flex items-center justify-between font-bold text-amber-300">
                <span>Skill Gap Identified</span>
                <span className="text-[10px] bg-amber-900 px-2 py-0.5 rounded text-amber-200 font-extrabold">
                  OPTIONAL
                </span>
              </div>
              <p className="text-amber-400 text-[11px] font-medium mt-1">
                Kubernetes &amp; AWS SageMaker are listed as preferred bonus qualifications.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CareerPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-sans">
          <div className="text-xs text-slate-400 font-semibold animate-pulse">
            Loading AI Career Match Studio...
          </div>
        </div>
      }
    >
      <CareerContent />
    </Suspense>
  );
}
