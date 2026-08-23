"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Save, Sparkles } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function EditJobPostingPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;

  const todayStr = new Date().toISOString().split("T")[0];

  const [formData, setFormData] = useState({
    title: "",
    department: "Engineering",
    location: "San Francisco, CA",
    work_mode: "Hybrid",
    employment_type: "FULL_TIME",
    experience: "3-5 Years",
    date_posted: todayStr,
    closing_date: "",
    status: "PUBLISHED",
    key_skills: "Python, FastAPI, PostgreSQL, RAG",
    preferred_skills: "Kubernetes, Docker, Vector DBs, MLOps",
    good_to_have: "Kafka, Redis, GraphQL, Terraform",
    responsibilities:
      "• Design, build, and deploy production-grade AI & RAG microservices\n• Lead API design and high-throughput vector search pipelines\n• Collaborate with product engineering to optimize candidate matching algorithms",
    about_company:
      "AuraHire AI is an enterprise talent intelligence platform powering automated candidate matching, explainable scoring, and end-to-end recruitment workflows.",
    description: "",
  });

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch existing job details on load
  useEffect(() => {
    async function loadJobDetails() {
      if (!jobId) return;
      try {
        const res = await apiFetch(`/api/v1/jobs/${jobId}`);
        if (res.ok) {
          const job = await res.json();
          let parsedWorkMode = "Hybrid";
          let parsedLocation = job.location || "Remote";

          if (job.location?.includes("(Remote)")) {
            parsedWorkMode = "Remote";
            parsedLocation = job.location.replace(" (Remote)", "");
          } else if (job.location?.includes("(On-site)")) {
            parsedWorkMode = "On-site";
            parsedLocation = job.location.replace(" (On-site)", "");
          } else if (job.location?.includes("(Hybrid)")) {
            parsedWorkMode = "Hybrid";
            parsedLocation = job.location.replace(" (Hybrid)", "");
          }

          let parsedExp = "3-5 Years";
          if (job.description && job.description.includes("Required Experience**: ")) {
            const match = job.description.match(/Required Experience\*\*: ([^\n]+)/);
            if (match && match[1]) {
              parsedExp = match[1].trim();
            }
          }

          setFormData((prev) => ({
            ...prev,
            title: job.title || "",
            department: job.department || "Engineering",
            location: parsedLocation,
            work_mode: parsedWorkMode,
            employment_type: job.employment_type || "FULL_TIME",
            experience: parsedExp,
            status: job.status || "PUBLISHED",
            description: job.description || "",
          }));
        }
      } catch (err) {
        console.error("Error loading job details for editing:", err);
      } finally {
        setFetching(false);
      }
    }
    loadJobDetails();
  }, [jobId]);

  // Auto-compile markdown if individual fields update
  useEffect(() => {
    if (fetching) return;
    const compiledMarkdown = `## About the Company
${formData.about_company}

## Work Location & Schedule
- **Location**: ${formData.location} (${formData.work_mode})
- **Required Experience**: ${formData.experience}
- **Date Posted**: ${formData.date_posted}
${formData.closing_date ? `- **Application Closing Date**: ${formData.closing_date}` : ""}

## Key Responsibilities
${formData.responsibilities}

## Required Key Skills
${formData.key_skills
  .split(",")
  .map((s) => `- ${s.trim()}`)
  .filter(Boolean)
  .join("\n")}

## Preferred Qualifications & Skills
${formData.preferred_skills
  .split(",")
  .map((s) => `- ${s.trim()}`)
  .filter(Boolean)
  .join("\n")}

## Good to Have Knowledge
${formData.good_to_have
  .split(",")
  .map((s) => `- ${s.trim()}`)
  .filter(Boolean)
  .join("\n")}`;

    setFormData((prev) => ({ ...prev, description: compiledMarkdown }));
  }, [
    fetching,
    formData.about_company,
    formData.location,
    formData.work_mode,
    formData.experience,
    formData.date_posted,
    formData.closing_date,
    formData.responsibilities,
    formData.key_skills,
    formData.preferred_skills,
    formData.good_to_have,
  ]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.description) {
      setError("Job title and description are required.");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const formattedLocation = `${formData.location} (${formData.work_mode})`;

      const payload = {
        title: formData.title,
        department: formData.department,
        location: formattedLocation,
        employment_type: formData.employment_type,
        status: formData.status,
        description: formData.description,
      };

      const res = await apiFetch(`/api/v1/jobs/${jobId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: null }));
        throw new Error(errData.detail || "Failed to update job posting.");
      }

      router.push("/recruiter/jobs");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update job posting.");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="min-h-screen bg-[#0b1220] text-slate-100 p-8 flex items-center justify-center font-sans">
        <div className="text-xs text-slate-400 font-semibold animate-pulse">
          Loading job requisition details...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Edit Job Requisition
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Update job specifications, required experience, skills, and requirements.
            </p>
          </div>
          <Link href="/recruiter/jobs" className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
            <ArrowLeft size={14} /> Cancel
          </Link>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-4 rounded-lg">
            {error}
          </div>
        )}

        {/* Form Container */}
        <form onSubmit={handleSubmit} className="bg-[#111a2c] border border-[#233047] rounded-xl p-6 md:p-8 space-y-6 shadow-xl">
          {/* Section 1: Basic Information */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              1. Basic Information
            </h3>

            <div>
              <label htmlFor="edit-job-title-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Job Title *
              </label>
              <input
                id="edit-job-title-input"
                name="title"
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="edit-job-department-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Department
                </label>
                <input
                  id="edit-job-department-input"
                  name="department"
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="edit-job-location-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Location
                </label>
                <input
                  id="edit-job-location-input"
                  name="location"
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label htmlFor="edit-job-work-mode-select" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Work Mode
                </label>
                <select
                  id="edit-job-work-mode-select"
                  name="work_mode"
                  value={formData.work_mode}
                  onChange={(e) => setFormData({ ...formData, work_mode: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="Hybrid">Hybrid</option>
                  <option value="Remote">Remote</option>
                  <option value="On-site">On-site</option>
                </select>
              </div>

              <div>
                <label htmlFor="edit-job-employment-type-select" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Employment Type
                </label>
                <select
                  id="edit-job-employment-type-select"
                  name="employment_type"
                  value={formData.employment_type}
                  onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="FULL_TIME">Full-time</option>
                  <option value="PART_TIME">Part-time</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="INTERNSHIP">Internship</option>
                </select>
              </div>

              <div>
                <label htmlFor="edit-job-experience-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Required Experience
                </label>
                <input
                  id="edit-job-experience-input"
                  name="experience"
                  type="text"
                  placeholder="e.g. 3-5 Years"
                  value={formData.experience}
                  onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="edit-job-status-select" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Status
                </label>
                <select
                  id="edit-job-status-select"
                  name="status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="PUBLISHED">Published</option>
                  <option value="DRAFT">Draft</option>
                  <option value="PAUSED">Paused</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: Full Description Editor */}
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <label htmlFor="edit-job-description-textarea" className="block text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              2. Job Requisition Description (Markdown)
            </label>

            <div>
              <textarea
                id="edit-job-description-textarea"
                name="description"
                rows={12}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500 transition leading-relaxed"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="pt-6 border-t border-slate-800 flex items-center justify-end gap-3">
            <Link
              href="/recruiter/jobs"
              className="px-5 py-2.5 rounded-lg border border-slate-700 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 transition"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-lg shadow-emerald-500/20"
            >
              <Save size={14} />
              {loading ? "Saving Changes..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
