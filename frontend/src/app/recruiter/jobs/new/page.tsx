"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles, FileText } from "lucide-react";
import { apiFetch, getOrgId, setOrgId } from "@/lib/api";

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
    openings: "1",
    date_posted: todayStr,
    closing_date: "",
    status: "DRAFT",
    key_skills: "Python, FastAPI, PostgreSQL, RAG",
    preferred_skills:
      "• Experience with Kubernetes, Docker, or containerization\n• Knowledge of Vector Databases & LLM orchestration\n• Familiarity with MLOps pipelines and cloud architecture",
    good_to_have:
      "• Experience working on payment platforms, fintech products, or financial technology solutions\n• Knowledge of Kubernetes, messaging systems, or distributed systems\n• Familiarity with CI/CD pipelines, monitoring, and observability tools\n• Experience working with high-volume transaction processing systems\n• Understanding of security, scalability, and reliability requirements in fintech applications",
    responsibilities:
      "• Design, build, and deploy production-grade AI & RAG microservices\n• Lead API design and high-throughput vector search pipelines\n• Collaborate with product engineering to optimize candidate matching algorithms",
    about_company:
      "AuraHire AI is an enterprise talent intelligence platform powering automated candidate matching, explainable scoring, and end-to-end recruitment workflows.",
    salary: "",
    company_website: "",
    description: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-generate Markdown description whenever individual fields update
  useEffect(() => {
    const formattedPreferredSkills =
      formData.preferred_skills.includes("•") || formData.preferred_skills.includes("-")
        ? formData.preferred_skills
        : formData.preferred_skills
            .split(",")
            .map((s) => `• ${s.trim()}`)
            .filter(Boolean)
            .join("\n");

    const compiledMarkdown = `## About the Company
${formData.about_company}

## Work Location & Schedule
- **Location**: ${formData.location} (${formData.work_mode})
- **Required Experience**: ${formData.experience}
${formData.openings ? `- **Number of Openings**: ${formData.openings}` : ""}
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
${formattedPreferredSkills}

## Good to Have Knowledge
${formData.good_to_have}`;

    setFormData((prev) => ({ ...prev, description: compiledMarkdown }));
  }, [
    formData.about_company,
    formData.location,
    formData.work_mode,
    formData.experience,
    formData.openings,
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
      let currentOrgId = getOrgId();
      if (!currentOrgId) {
        try {
          const meRes = await apiFetch("/api/v1/auth/me");
          if (meRes.ok) {
            const meData = await meRes.json();
            if (meData.memberships && meData.memberships.length > 0 && meData.memberships[0].organization_id) {
              currentOrgId = meData.memberships[0].organization_id;
              if (currentOrgId) setOrgId(currentOrgId);
            }
          }
        } catch {}
      }

      const formattedLocation = `${formData.location} (${formData.work_mode})`;

      const payload = {
        title: formData.title,
        department: formData.department,
        location: formattedLocation,
        employment_type: formData.employment_type,
        status: formData.status,
        verification_status: "DRAFT",
        salary: formData.salary,
        company_website: formData.company_website,
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
      setError(
        err instanceof Error ? err.message : "Failed to create job posting.",
      );
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
              Define job specifications, key skills, responsibilities, required
              experience, and tenant requirements.
            </p>
          </div>
          <Link
            href="/recruiter/jobs"
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
          >
            <ArrowLeft size={14} /> Cancel
          </Link>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs p-4 rounded-lg">
            {error}
          </div>
        )}

        {/* Form Container */}
        <form
          onSubmit={handleSubmit}
          className="bg-[#111a2c] border border-[#233047] rounded-xl p-6 md:p-8 space-y-6 shadow-xl"
        >
          {/* Section 1: Basic Information */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2">
              1. Basic Information
            </h3>

            <div>
              <label htmlFor="job-title-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Job Title *
              </label>
              <input
                id="job-title-input"
                name="title"
                type="text"
                required
                placeholder="e.g. Staff Backend Engineer - Python"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="job-department-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Department
                </label>
                <input
                  id="job-department-input"
                  name="department"
                  type="text"
                  placeholder="e.g. UG/PG - ANY DEPARTMENT"
                  value={formData.department}
                  onChange={(e) =>
                    setFormData({ ...formData, department: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="job-location-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Location (Area / City Name)
                </label>
                <input
                  id="job-location-input"
                  name="location"
                  type="text"
                  placeholder="e.g. Bengaluru, KA"
                  value={formData.location}
                  onChange={(e) =>
                    setFormData({ ...formData, location: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label htmlFor="job-work-mode-select" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Role Type (Work Mode)
                </label>
                <select
                  id="job-work-mode-select"
                  name="work_mode"
                  value={formData.work_mode}
                  onChange={(e) =>
                    setFormData({ ...formData, work_mode: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="Hybrid">Hybrid</option>
                  <option value="Remote">Remote</option>
                  <option value="On-site">On-site</option>
                </select>
              </div>

              <div>
                <label htmlFor="job-employment-type-select" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Employment Type
                </label>
                <select
                  id="job-employment-type-select"
                  name="employment_type"
                  value={formData.employment_type}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      employment_type: e.target.value,
                    })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="FULL_TIME">Full-time</option>
                  <option value="PART_TIME">Part-time</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="INTERNSHIP">Internship</option>
                </select>
              </div>

              <div>
                <label htmlFor="job-experience-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Required Experience
                </label>
                <input
                  id="job-experience-input"
                  name="experience"
                  type="text"
                  placeholder="e.g. 3-5 Years or 5+ yrs"
                  value={formData.experience}
                  onChange={(e) =>
                    setFormData({ ...formData, experience: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="job-status-select" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Initial Status
                </label>
                <select
                  id="job-status-select"
                  name="status"
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                >
                  <option value="DRAFT">Draft</option>
                  <option value="PUBLISHED">Published (Active)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="job-date-posted-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Date Posted
                </label>
                <input
                  id="job-date-posted-input"
                  name="date_posted"
                  type="date"
                  value={formData.date_posted}
                  onChange={(e) =>
                    setFormData({ ...formData, date_posted: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="job-closing-date-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Closing Date (Optional)
                </label>
                <input
                  id="job-closing-date-input"
                  name="closing_date"
                  type="date"
                  value={formData.closing_date}
                  onChange={(e) =>
                    setFormData({ ...formData, closing_date: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="job-salary-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Salary / Compensation Range (Optional)
                </label>
                <input
                  id="job-salary-input"
                  name="salary"
                  type="text"
                  placeholder="e.g. ₹12 - ₹18 LPA or $120k - $150k"
                  value={formData.salary || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, salary: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="job-openings-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  No. of Openings (Optional)
                </label>
                <input
                  id="job-openings-input"
                  name="openings"
                  type="number"
                  min={1}
                  placeholder="e.g. 5"
                  value={formData.openings || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, openings: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="job-company-website-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Company Website URL (Optional)
                </label>
                <input
                  id="job-company-website-input"
                  name="company_website"
                  type="url"
                  placeholder="e.g. https://www.avenuesai.com"
                  value={formData.company_website || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, company_website: e.target.value })
                  }
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
              <label htmlFor="job-key-skills-input" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Key Skills (Comma Separated) *
              </label>
              <input
                id="job-key-skills-input"
                name="key_skills"
                type="text"
                required
                placeholder="e.g. Python,SQL,react,FastAPI"
                value={formData.key_skills}
                onChange={(e) =>
                  setFormData({ ...formData, key_skills: e.target.value })
                }
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="job-preferred-skills-textarea" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Preferred Skills (Bullet points)
                </label>
                <textarea
                  id="job-preferred-skills-textarea"
                  name="preferred_skills"
                  rows={4}
                  placeholder="• Experience with Kubernetes, Docker, or containerization&#10;• Knowledge of Vector Databases & LLM orchestration&#10;• MLOps pipelines and cloud architecture"
                  value={formData.preferred_skills}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      preferred_skills: e.target.value,
                    })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label htmlFor="job-good-to-have-textarea" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Good to Have Knowledge In (Bullet points)
                </label>
                <textarea
                  id="job-good-to-have-textarea"
                  name="good_to_have"
                  rows={4}
                  placeholder="• Experience working on payment platforms, fintech products..."
                  value={formData.good_to_have}
                  onChange={(e) =>
                    setFormData({ ...formData, good_to_have: e.target.value })
                  }
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-sm text-white focus:outline-none focus:border-sky-500 transition"
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
              <label htmlFor="job-responsibilities-textarea" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Core Responsibilities (Bullet points)
              </label>
              <textarea
                id="job-responsibilities-textarea"
                name="responsibilities"
                rows={4}
                placeholder="• List key duties..."
                value={formData.responsibilities}
                onChange={(e) =>
                  setFormData({ ...formData, responsibilities: e.target.value })
                }
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>

            <div>
              <label htmlFor="job-about-company-textarea" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                About Company & Context
              </label>
              <textarea
                id="job-about-company-textarea"
                name="about_company"
                rows={3}
                placeholder="Brief description of your organization..."
                value={formData.about_company}
                onChange={(e) =>
                  setFormData({ ...formData, about_company: e.target.value })
                }
                className="w-full bg-[#0b1425] border border-[#233047] rounded-lg p-4 text-sm text-white focus:outline-none focus:border-sky-500 transition"
              />
            </div>
          </div>

          {/* Section 4: Compiled Job Description (Markdown Review & Edit) */}
          <div className="space-y-3 pt-4 border-t border-slate-800">
            <label htmlFor="job-compiled-description-textarea" className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <FileText size={14} /> 4. Compiled Job Description{" "}
              </span>
              <span className="text-[10px] text-slate-400 font-normal">
                Auto-assembled & fully customizable Markdown
              </span>
            </label>

            <textarea
              id="job-compiled-description-textarea"
              name="description"
              required
              rows={8}
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
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
