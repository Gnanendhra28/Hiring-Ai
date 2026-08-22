"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import {
  ArrowLeft,
  Bookmark,
  Briefcase,
  CheckCircle2,
  Clock,
  ExternalLink,
  MapPin,
  Sparkles,
  Star,
} from "lucide-react";

export default function PublicJobDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [applied, setApplied] = useState(false);
  const [saved, setSaved] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchJob() {
      if (!slug) return;
      try {
        const res = await apiFetch(`/api/v1/jobs/${slug}`);
        if (res.ok) {
          const data = await res.json();
          setJob(data);
        }
      } catch (err) {
        console.error("Error fetching job:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchJob();
  }, [slug]);

  // Determine if application closing date has passed
  const parseClosingDate = () => {
    if (!job?.description) return { dateStr: null, isClosed: false };
    const match = job.description.match(/Application Closing Date\*\*: ([^\n]+)/);
    if (!match || !match[1]) return { dateStr: null, isClosed: false };

    const raw = match[1].trim();
    let closingDt: Date | null = null;

    if (raw.includes("-")) {
      closingDt = new Date(raw);
    } else if (raw.includes("/")) {
      const parts = raw.split("/");
      if (parts.length === 3) {
        closingDt = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
      }
    }

    if (closingDt && !isNaN(closingDt.getTime())) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return { dateStr: raw, isClosed: today > closingDt };
    }

    return { dateStr: raw, isClosed: false };
  };

  const { dateStr: closingDateStr, isClosed: isDateExpired } = parseClosingDate();
  const isClosed = isDateExpired || job?.status === "CLOSED";

  const handleApply = async () => {
    if (isClosed) return;
    setSubmitting(true);
    setError(null);

    try {
      if (job?.id) {
        const res = await apiFetch("/api/v1/candidate/applications", {
          method: "POST",
          body: JSON.stringify({ job_id: job.id }),
        });
        if (res.ok) {
          setApplied(true);
        } else {
          const errData = await res.json().catch(() => ({ detail: null }));
          throw new Error(errData.detail || "Failed to submit application.");
        }
      } else {
        setApplied(true);
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit application.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex items-center justify-center font-sans">
        <div className="text-xs text-slate-400 font-semibold animate-pulse">
          Loading job details...
        </div>
      </div>
    );
  }

  const companyName = job?.department || "Avenues AI Limited";
  const title = job?.title || "Software Development Engineer";
  const location = job?.location || "Bengaluru";
  const rawDescription = job?.description || "";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link
          href="/jobs"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          <ArrowLeft size={15} /> View All Jobs
        </Link>

        {/* IMAGE 1 REFERENCE: Top Job Header Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1.5 min-w-0 flex-1">
              <h1 className="text-2xl sm:text-3xl font-bold text-white">
                {title}
              </h1>

              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-300 font-medium">
                <span className="font-semibold text-slate-200">{companyName}</span>
                <span className="flex items-center gap-1 text-amber-400 font-bold">
                  <Star size={13} className="fill-amber-400" /> 4.1
                </span>
                <span className="text-slate-500">|</span>
                <span className="text-slate-400">4 Reviews</span>
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-2 font-medium">
                <span className="flex items-center gap-1.5">
                  <Briefcase size={14} className="text-slate-400" /> 0 - 3 years
                </span>
                <span className="text-slate-600">|</span>
                <span className="text-slate-300 font-semibold">₹ Not Disclosed</span>
              </div>

              <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-300 pt-1 font-medium">
                <MapPin size={14} className="text-slate-400 shrink-0" />
                <span>{location}</span>
              </div>
            </div>

            {/* Company Logo Badge on Right */}
            <div className="w-16 h-16 rounded-2xl bg-indigo-950 border border-indigo-800 text-indigo-300 font-extrabold text-2xl grid place-items-center shrink-0 shadow-md">
              {companyName[0] || "A"}
            </div>
          </div>

          <div className="flex justify-end">
            <a
              href="#send-jobs"
              className="text-xs font-bold text-indigo-400 hover:underline flex items-center gap-1"
            >
              Send me jobs like this
            </a>
          </div>

          {/* Card Divider */}
          <hr className="border-slate-800" />

          {/* Bottom Card Footer Row: Posted metadata & Action Buttons */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-medium">
              <span>
                Posted: <strong className="text-slate-200">2 days ago</strong>
              </span>
              <span className="text-slate-700">|</span>
              <span>
                Openings: <strong className="text-slate-200">2</strong>
              </span>
              <span className="text-slate-700">|</span>
              <span>
                Applicants: <strong className="text-slate-200">100+</strong>
              </span>
              {closingDateStr && (
                <>
                  <span className="text-slate-700">|</span>
                  <span className={`font-mono ${isClosed ? "text-rose-400 font-bold" : "text-slate-300"}`}>
                    Closing Date: {closingDateStr}
                  </span>
                </>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setSaved(!saved)}
                className={`px-5 py-2.5 rounded-full text-xs font-bold border transition-all flex items-center gap-1.5 ${
                  saved
                    ? "bg-indigo-950 border-indigo-700 text-indigo-300"
                    : "border-slate-700 text-slate-200 hover:bg-slate-800"
                }`}
              >
                <Bookmark size={14} /> {saved ? "Saved" : "Save"}
              </button>

              {isClosed ? (
                <div className="px-5 py-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-full text-xs font-bold flex items-center gap-1.5 cursor-not-allowed">
                  <span>🔒 Applications Closed</span>
                </div>
              ) : applied ? (
                <div className="px-6 py-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-full text-xs font-bold flex items-center gap-1.5">
                  <CheckCircle2 size={15} /> Application Submitted
                </div>
              ) : (
                <button
                  onClick={handleApply}
                  disabled={submitting}
                  className="px-7 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-full text-xs font-bold shadow-lg shadow-blue-600/30 transition-all disabled:opacity-50"
                >
                  {submitting ? "Submitting..." : "Apply"}
                </button>
              )}

              {!isClosed && (
                <Link
                  href={`/career?jobId=${job?.id || slug}`}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 transition-all"
                >
                  <Sparkles size={14} /> Apply with AI
                </Link>
              )}
            </div>
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-semibold">
              {error}
            </div>
          )}
        </div>

        {/* IMAGE 2 & 3 REFERENCE: Main Structured Job Description Body */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 space-y-8 shadow-2xl">
          {/* Section Heading */}
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-white">Job description</h2>
            <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
            <p className="text-xs text-slate-400 font-medium">Location: {location}</p>
          </div>

          {/* Overview Paragraph */}
          <div className="space-y-2 text-xs text-slate-300 leading-relaxed font-normal">
            <p>
              <strong className="text-white">{companyName}</strong>, formerly known as{" "}
              <strong className="text-white">Infibeam Avenues Limited</strong>, is looking for a{" "}
              <strong className="text-white">{title}</strong> to work on scalable fintech, payment platforms, and enterprise-grade software systems. The role involves designing, developing, and maintaining high-performance applications and backend services that power large-scale digital payment and financial technology ecosystems.
            </p>
            <p className="pt-1 text-slate-400 font-medium flex items-center gap-1">
              Website:{" "}
              <a
                href="https://www.avenuesai.com"
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 hover:underline flex items-center gap-1 font-semibold"
              >
                https://www.avenuesai.com <ExternalLink size={12} />
              </a>
            </p>
          </div>

          {/* Roles & Responsibilities */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-white">Roles &amp; Responsibilities</h3>
            <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Design, develop, and maintain scalable backend/fullstack applications</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Build and manage microservices-based architectures</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Develop secure, high-performance APIs and payment-related services</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Work on software architecture, system design, and performance optimization</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Collaborate with cross-functional teams to deliver reliable software solutions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Troubleshoot production issues and improve system reliability and scalability</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Write clean, maintainable, and efficient code following engineering best practices</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Participate in code reviews, technical discussions, and architectural decisions</span>
              </li>
            </ul>
          </div>

          {/* Required Skills & Qualifications */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-white">Required Skills &amp; Qualifications</h3>
            <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Strong experience in Java/Python/PHP and similar backend technologies</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>BE/B.Tech in Computer Science, Information Technology, or a related field, preferably from reputed institutes</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Good knowledge of FastAPI / Spring Boot, Microservices Architecture, and REST APIs</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Exposure to frontend technologies such as JavaScript, React, or similar technologies</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Experience with Docker and cloud/deployment environments</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Strong understanding of databases, system design, and scalable application development</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Understanding of SDLC, debugging, performance optimization, and production support</span>
              </li>
            </ul>
          </div>

          {/* Good to Have */}
          <div className="space-y-3">
            <h3 className="text-sm font-bold text-white">Good to Have</h3>
            <ul className="space-y-2 text-xs text-slate-300 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Experience working on payment platforms, fintech products, or financial technology solutions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Knowledge of Kubernetes, messaging systems, or distributed systems</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Familiarity with CI/CD pipelines, monitoring, and observability tools</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Experience working with high-volume transaction processing systems</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 font-bold">•</span>
                <span>Understanding of security, scalability, and reliability requirements in fintech applications</span>
              </li>
            </ul>
          </div>

          {/* Role Metadata Specification Table (IMAGE 3) */}
          <div className="space-y-2 text-xs text-slate-300 border-t border-slate-800 pt-6">
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Role:</span>
              <span className="font-semibold text-white">Back End Developer</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Industry Type:</span>
              <span className="font-semibold text-white">FinTech / Payments / AI Systems</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Department:</span>
              <span className="font-semibold text-white">Engineering - Software &amp; QA</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Employment Type:</span>
              <span className="font-semibold text-white">Full Time, Permanent</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-[140px_1fr] gap-2 py-1">
              <span className="font-semibold text-slate-400">Role Category:</span>
              <span className="font-semibold text-white">Software Development</span>
            </div>
          </div>

          {/* Education */}
          <div className="space-y-1 border-t border-slate-800 pt-6">
            <h4 className="text-xs font-bold text-white">Education</h4>
            <p className="text-xs text-slate-300 font-medium">
              <strong className="text-slate-200">UG:</strong> B.Tech / B.E. in Computer Science and Engineering (CSE), Information Technology
            </p>
          </div>

          {/* Key Skills */}
          <div className="space-y-3 border-t border-slate-800 pt-6">
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-white">Key Skills</h4>
              <p className="text-[11px] text-slate-400">Skills highlighted with &lsquo;★&rsquo; are preferred keyskills</p>
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              {["★ Java", "★ Backend Development", "★ Python", "★ FastAPI", "C++", "Docker", "PostgreSQL", "REST APIs"].map((skill) => (
                <span
                  key={skill}
                  className="px-4 py-1.5 rounded-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-semibold hover:border-indigo-500 transition-all"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>

          {/* Raw Description Appendix */}
          {rawDescription && (
            <div className="border-t border-slate-800/80 pt-6 space-y-2">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400">
                Full Employer Specification Note
              </h4>
              <div className="whitespace-pre-line text-xs font-mono text-slate-400 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 leading-relaxed">
                {rawDescription}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
