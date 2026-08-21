"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Clock,
  ExternalLink,
  Globe,
  Lock,
  Mail,
  Phone,
  Save,
  ShieldCheck,
  Sparkles,
  User,
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";
import {
  fetchRecruiterProfile,
  updateRecruiterProfile,
  submitEmployerVerification,
  RecruiterProfileData,
} from "@/lib/api";

export default function EmployerProfilePage() {
  const { user } = useAuth();

  const [formData, setFormData] = useState({
    job_title: "Head of Talent Acquisition",
    department: "Engineering & Operations",
    phone_number: "+91 98765 43210",
    company_name: "Rao Enterprise",
    website_url: "https://raoenterprise.com",
    registration_id: "CIN-U72200KA2026PTC123456",
    linkedin_url: "https://linkedin.com/company/rao-enterprise",
  });

  const [verificationStatus, setVerificationStatus] = useState<string>("UNVERIFIED");
  const [submittedAt, setSubmittedAt] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await fetchRecruiterProfile();
        if (data) {
          setFormData({
            job_title: data.job_title || "Head of Talent Acquisition",
            department: data.department || "Engineering & Operations",
            phone_number: data.phone_number || "+91 98765 43210",
            company_name: data.company_name || "Rao Enterprise",
            website_url: data.website_url || "https://raoenterprise.com",
            registration_id: data.registration_id || "CIN-U72200KA2026PTC123456",
            linkedin_url: data.linkedin_url || "https://linkedin.com/company/rao-enterprise",
          });
          setVerificationStatus(data.verification_status || "UNVERIFIED");
          setSubmittedAt(data.submitted_at || null);
        }
      } catch (err) {
        console.error("Error loading recruiter profile:", err);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      const updated = await updateRecruiterProfile(formData);
      if (updated) {
        setMessage({ type: "success", text: "Profile details saved successfully." });
      } else {
        throw new Error("Failed to save profile changes.");
      }
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Error saving profile details." });
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitVerification = async () => {
    if (!formData.company_name || !formData.registration_id) {
      setMessage({
        type: "error",
        text: "Please provide Company Name and Registration / Tax ID before submitting for admin verification.",
      });
      return;
    }

    setSubmitting(true);
    setMessage(null);

    try {
      // First save profile fields
      await updateRecruiterProfile(formData);
      // Then submit for verification
      const res = await submitEmployerVerification();
      if (res) {
        setVerificationStatus("PENDING_VERIFICATION");
        setSubmittedAt(res.submitted_at || new Date().toISOString());
        setMessage({
          type: "success",
          text: "Your employer profile has been submitted to Platform Admin for verification!",
        });
      } else {
        throw new Error("Failed to submit verification request.");
      }
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Error submitting profile for verification." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <ShieldCheck className="text-sky-400" size={24} /> Employer Profile & Verification
            </h1>
            <p className="text-slate-400 text-xs mt-1">
              Create and manage your employer identity and submit company credentials for Admin verification.
            </p>
          </div>
          <Link href="/recruiter/dashboard" className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
        </div>

        {/* Verification Status Banner */}
        <div
          className={`p-5 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg ${
            verificationStatus === "APPROVED" || verificationStatus === "VERIFIED"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : verificationStatus === "PENDING_VERIFICATION"
              ? "bg-amber-500/10 border-amber-500/30 text-amber-300"
              : "bg-blue-500/10 border-blue-500/30 text-sky-300"
          }`}
        >
          <div className="flex items-start gap-3">
            <div className="mt-0.5">
              {verificationStatus === "APPROVED" || verificationStatus === "VERIFIED" ? (
                <CheckCircle2 className="text-emerald-400" size={22} />
              ) : verificationStatus === "PENDING_VERIFICATION" ? (
                <Clock className="text-amber-400 animate-pulse" size={22} />
              ) : (
                <ShieldCheck className="text-sky-400" size={22} />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-sm text-white">
                  {verificationStatus === "APPROVED" || verificationStatus === "VERIFIED"
                    ? "Verified Real Employer"
                    : verificationStatus === "PENDING_VERIFICATION"
                    ? "Submitted to Admin for Verification"
                    : "Unverified Employer Profile"}
                </h3>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                    verificationStatus === "APPROVED" || verificationStatus === "VERIFIED"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : verificationStatus === "PENDING_VERIFICATION"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : "bg-slate-800 text-slate-400 border border-slate-700"
                  }`}
                >
                  {verificationStatus}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {verificationStatus === "APPROVED" || verificationStatus === "VERIFIED"
                  ? "Your employer identity and company registration have been verified by Platform Admin."
                  : verificationStatus === "PENDING_VERIFICATION"
                  ? `Submitted on ${submittedAt ? new Date(submittedAt).toLocaleDateString() : "today"}. Admin verification review is in progress.`
                  : "Complete your personal identity and company credentials below, then submit to Admin for verification."}
              </p>
            </div>
          </div>

          {verificationStatus !== "APPROVED" && verificationStatus !== "VERIFIED" && (
            <button
              type="button"
              onClick={handleSubmitVerification}
              disabled={submitting || verificationStatus === "PENDING_VERIFICATION"}
              className={`px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition shadow-md whitespace-nowrap ${
                verificationStatus === "PENDING_VERIFICATION"
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                  : "bg-blue-600 hover:bg-blue-500 text-white"
              }`}
            >
              <Sparkles size={14} />
              {submitting
                ? "Submitting..."
                : verificationStatus === "PENDING_VERIFICATION"
                ? "Awaiting Admin Review"
                : "Submit to Admin for Verification"}
            </button>
          )}
        </div>

        {message && (
          <div
            className={`p-4 rounded-lg text-xs border ${
              message.type === "success"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-red-500/10 border-red-500/30 text-red-400"
            }`}
          >
            {message.text}
          </div>
        )}

        {/* Profile Edit Form */}
        <form onSubmit={handleSaveProfile} className="bg-[#111a2c] border border-[#233047] rounded-xl p-6 md:p-8 space-y-6 shadow-xl">
          {/* Section 1: Personal & Account Identity */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
              <User size={15} /> 1. Recruiter & Personal Information
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  disabled
                  value={user?.full_name || "Santhosha Rao"}
                  className="w-full bg-[#080e1a] border border-[#1b263b] rounded-lg px-4 py-2.5 text-sm text-slate-400 cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Work Email
                </label>
                <input
                  type="email"
                  disabled
                  value={user?.email || "gnanendhrakeys@gmail.com"}
                  className="w-full bg-[#080e1a] border border-[#1b263b] rounded-lg px-4 py-2.5 text-sm text-slate-400 cursor-not-allowed"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Job Title / Designation *
                </label>
                <input
                  type="text"
                  required
                  value={formData.job_title}
                  onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                  placeholder="e.g. Head of Talent Acquisition"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Department
                </label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  placeholder="e.g. Engineering & HR"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Contact Phone Number *
                </label>
                <input
                  type="text"
                  required
                  value={formData.phone_number}
                  onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                  placeholder="e.g. +91 98765 43210"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Company & Verification Credentials */}
          <div className="space-y-4 pt-4 border-t border-slate-800">
            <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center gap-2">
              <Building2 size={15} /> 2. Company & Business Credentials
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Company Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  placeholder="e.g. Rao Enterprise"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Company Website URL
                </label>
                <input
                  type="url"
                  value={formData.website_url}
                  onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                  placeholder="e.g. https://raoenterprise.com"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Registration / GSTIN / Tax ID *
                </label>
                <input
                  type="text"
                  required
                  value={formData.registration_id}
                  onChange={(e) => setFormData({ ...formData, registration_id: e.target.value })}
                  placeholder="e.g. CIN-U72200KA2026PTC123456"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Official Company LinkedIn URL
                </label>
                <input
                  type="url"
                  value={formData.linkedin_url}
                  onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                  placeholder="e.g. https://linkedin.com/company/rao-enterprise"
                  className="w-full bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500 transition"
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-800">
            <button
              type="button"
              onClick={handleSubmitVerification}
              disabled={submitting || verificationStatus === "PENDING_VERIFICATION"}
              className="px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-lg text-xs font-medium transition"
            >
              Submit to Admin for Verification
            </button>

            <div className="flex gap-3">
              <Link
                href="/recruiter/dashboard"
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition shadow-lg flex items-center gap-2"
              >
                <Save size={14} />
                {saving ? "Saving..." : "Save Profile Details"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
