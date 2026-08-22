"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles, FileText } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function CreateJobPostingPage() {
  const router = useRouter();

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
    status: "DRAFT",
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
  const [error, setError] = useState<string | null>(null);

  // Auto-generate Markdown description whenever individual fields update
  useEffect(() => {
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
      setError("Job title and core requirements are required.");
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
        verification_status: "PENDING_VERIFICATION",
        description: formData.description,
      };

      const res = await apiFetch("/api/v1/jobs", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: null }));
        throw new Error(errData.detail || "Failed to create job requisition.");
      }

      router.push("/recruiter/jobs");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create job posting.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Create New Requisition
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Define job specifications, key skills, responsibilities, required experience, and tenant requirements.
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
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Job Title *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Staff Backend Engineer - Python"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Department
                </label>
                <input
                  type="text"
                  placeholder="e.g. Engineering"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Location (Area / City Name)
                </label>
                <input
                  type="text"
                  placeholder="e.g. San Francisco, CA or Bengaluru, KA"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Role Type (Work Mode)
                </label>
                <select
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
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Employment Type
                </label>
                <select
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
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Required Experience
                </label>
                <input
                  type="text"
                  placeholder="e.g. 3-5 Years or 5+ yrs"
                  value={formData.experience}
                  onChange={(e) => setFormData({ ...formData, experience: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Initial Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="DRAFT">Draft</option>
                  <option value="PUBLISHED">Published (Active)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Date Posted
                </label>
                <input
                  type="date"
                  value={formData.date_posted}
                  onChange={(e) => setFormData({ ...formData, date_posted: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Closing Date (Optional)
                </label>
                <input
                  type="date"
                  value={formData.closing_date}
                  onChange={(e) => setFormData({ ...formData, closing_date: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Skills & Technical Qualifications */}
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              2. Skills & Technical Qualifications
            </h3>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Key Skills (Comma Separated) *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Python, FastAPI, PostgreSQL, RAG"
                value={formData.key_skills}
                onChange={(e) => setFormData({ ...formData, key_skills: e.target.value })}
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Preferred Skills
                </label>
                <input
                  type="text"
                  placeholder="e.g. Kubernetes, Docker, Vector DBs, MLOps"
                  value={formData.preferred_skills}
                  onChange={(e) => setFormData({ ...formData, preferred_skills: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Good to Have Knowledge In
                </label>
                <input
                  type="text"
                  placeholder="e.g. Kafka, Redis, GraphQL, Terraform"
                  value={formData.good_to_have}
                  onChange={(e) => setFormData({ ...formData, good_to_have: e.target.value })}
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Responsibilities & Company Context */}
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              3. Responsibilities & About Company
            </h3>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Core Responsibilities (Bullet points)
              </label>
              <textarea
                rows={4}
                placeholder="• List key duties..."
                value={formData.responsibilities}
                onChange={(e) => setFormData({ ...formData, responsibilities: e.target.value })}
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                About Company & Context
              </label>
              <textarea
                rows={3}
                placeholder="Brief description of your organization..."
                value={formData.about_company}
                onChange={(e) => setFormData({ ...formData, about_company: e.target.value })}
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>
          </div>

          {/* Section 4: Compiled Job Description (Markdown Review & Edit) */}
          <div className="space-y-3 pt-4 border-t border-slate-800">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5"><FileText size={14} /> 4. Compiled Job Description (Complete Description Review & Edit)</span>
              <span className="text-[10px] text-slate-400 font-normal">Auto-assembled & fully customizable Markdown</span>
            </h3>

            <textarea
              required
              rows={8}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full bg-[#070d18] border border-[#1b263b] rounded-lg p-4 text-xs font-mono text-slate-300 focus:outline-none focus:border-sky-500 transition leading-relaxed"
            />
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
              className="px-6 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-lg shadow-blue-500/20"
            >
              <Sparkles size={14} />
              {loading ? "Creating Requisition..." : "Create Job Requisition"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
