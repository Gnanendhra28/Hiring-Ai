"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth/AuthContext";
import {
  getCandidateProfile,
  updateCandidateProfile,
  CandidateProfileData,
} from "@/lib/api";

type SectionType =
  | "preferences"
  | "education"
  | "skills"
  | "languages"
  | "internships"
  | "projects"
  | "summary"
  | "accomplishments"
  | "employment"
  | "resume";

export default function CandidateProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<CandidateProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"view" | "insights">("view");
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Modal States
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [editingItem, setEditingItem] = useState<any>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  // Form states for profile header edit
  const [headerForm, setHeaderForm] = useState({
    headline: "",
    location: "",
    phone: "",
    degree: "",
    college: "",
    photo_url: "",
  });

  // Load Profile from Backend
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getCandidateProfile();
        if (data) {
          setProfile(data);
          setHeaderForm({
            headline: data.headline || "",
            location: data.location || "",
            phone: data.phone || "",
            degree: data.degree || "",
            college: data.college || "",
            photo_url: data.photo_url || "",
          });
        }
      } catch (err: any) {
        setError(err.message || "Failed to load candidate profile.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  // Helper to calculate profile completion percentage
  const calculateCompletion = (p: CandidateProfileData | null): number => {
    if (!p) return 0;
    let score = 0;
    let total = 9;

    if (user?.full_name && user?.email) score++;
    if (p.headline || p.location || p.phone) score++;
    if (p.degree || p.college || (p.education && p.education.length > 0)) score++;
    if (p.skills && p.skills.length > 0) score++;
    if (p.summary && p.summary.trim().length > 10) score++;
    if (p.career_preferences && Object.keys(p.career_preferences).length > 0) score++;
    if (p.projects && p.projects.length > 0) score++;
    if (p.employment && p.employment.length > 0 || (p.internships && p.internships.length > 0)) score++;
    if (p.resume_url || p.resume_filename) score++;

    return Math.round((score / total) * 100);
  };

  const saveProfileData = async (updatedFields: Partial<CandidateProfileData>, toastMsg: string) => {
    setSaving(true);
    setError(null);
    try {
      const result = await updateCandidateProfile(updatedFields);
      setProfile(result);
      showToast(toastMsg);
      setActiveModal(null);
      setEditingItem(null);
      setEditingIndex(null);
    } catch (err: any) {
      setError(err.message || "Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  // Quick Links Scroll Handler
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  if (loading) {
    return (
      <div className="py-12 px-4 max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="h-32 bg-slate-900/80 rounded-3xl border border-slate-800" />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="h-64 bg-slate-900/80 rounded-3xl border border-slate-800" />
          <div className="lg:col-span-3 space-y-6">
            <div className="h-48 bg-slate-900/80 rounded-3xl border border-slate-800" />
            <div className="h-48 bg-slate-900/80 rounded-3xl border border-slate-800" />
          </div>
        </div>
      </div>
    );
  }

  const completionPct = calculateCompletion(profile);

  return (
    <div className="py-8 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-6">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-20 right-6 z-50 p-4 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold shadow-2xl flex items-center space-x-2 animate-bounce">
          <span className="text-base">✓</span>
          <span>{toast}</span>
        </div>
      )}

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono mb-1.5">
            <span>CANDIDATE PORTAL</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Candidate Profile</h1>
        </div>

        <Link
          href="/candidate/dashboard"
          className="text-xs font-mono text-slate-400 hover:text-white hover:underline self-start sm:self-auto flex items-center gap-1"
        >
          ← Return to Dashboard
        </Link>
      </div>

      {/* Top Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("view")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "view"
              ? "bg-sky-500 text-white shadow-lg shadow-sky-500/20"
              : "text-slate-400 hover:text-white hover:bg-slate-900"
          }`}
        >
          View &amp; Edit
        </button>
        <button
          onClick={() => setActiveTab("insights")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "insights"
              ? "bg-sky-500 text-white shadow-lg shadow-sky-500/20"
              : "text-slate-400 hover:text-white hover:bg-slate-900"
          }`}
        >
          Activity Insights
        </button>
      </div>

      {/* Activity Insights Tab Content */}
      {activeTab === "insights" ? (
        <div className="glass-panel p-8 rounded-3xl border border-slate-800 text-center space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mx-auto text-xl font-bold">
            📊
          </div>
          <h3 className="text-xl font-bold text-white">Activity Insights &amp; Engagement</h3>
          <p className="text-slate-400 text-xs max-w-md mx-auto">
            View job application statuses, profile view metrics by recruiters, and assessment performance logs.
          </p>
          <div className="inline-block px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sky-400 text-xs font-mono">
            Status: Fully Operational — Track applications on your Dashboard
          </div>
        </div>
      ) : (
        /* Main View & Edit Tab Content */
        <div className="space-y-6">
          {/* Header Identity Card */}
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-2xl relative overflow-hidden">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
              <div className="flex items-center space-x-5">
                {/* Profile Photo / Avatar */}
                <div className="relative group">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white font-black text-2xl flex items-center justify-center border-2 border-slate-700 shadow-xl overflow-hidden">
                    {profile?.photo_url ? (
                      <img src={profile.photo_url} alt="Profile" className="w-full h-full object-cover" />
                    ) : (
                      <span>{user?.full_name ? user.full_name.charAt(0).toUpperCase() : "C"}</span>
                    )}
                  </div>
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-2xl font-black text-white">{user?.full_name || "Candidate Name"}</h2>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-mono">
                      Verified
                    </span>
                  </div>

                  <p className="text-sky-400 text-xs font-semibold mt-0.5">
                    {profile?.headline || "Professional Headline (e.g. Full Stack Developer)"}
                  </p>

                  {(profile?.degree || profile?.college) && (
                    <p className="text-slate-400 text-xs mt-1">
                      🎓 {profile?.degree || "Degree"} — {profile?.college || "College / University"}
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-2">
                    {profile?.location && <span>📍 {profile.location}</span>}
                    {profile?.phone && <span>📞 {profile.phone}</span>}
                    <span>✉ {user?.email}</span>
                  </div>
                </div>
              </div>

              {/* Action & Completion */}
              <div className="flex flex-col items-end space-y-3 self-stretch sm:self-auto justify-between sm:justify-start">
                <button
                  onClick={() => setActiveModal("header")}
                  className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold shadow-lg shadow-sky-500/20 transition-all flex items-center gap-1.5"
                >
                  ✏ Edit Profile
                </button>

                <div className="w-full sm:w-48 bg-slate-900/80 p-3 rounded-2xl border border-slate-800">
                  <div className="flex justify-between items-center text-[11px] font-mono mb-1">
                    <span className="text-slate-400">Completion</span>
                    <span className="text-sky-400 font-bold">{completionPct}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${completionPct}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Layout Grid: Quick Links Sidebar + Sections */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
            {/* Sidebar Quick Links Navigation */}
            <div className="lg:sticky lg:top-24 glass-panel p-4 rounded-3xl border border-slate-800 space-y-1 text-xs">
              <div className="px-3 py-1.5 text-[10px] font-mono uppercase text-slate-500 tracking-wider">
                Quick Navigation
              </div>
              <nav className="flex lg:flex-col overflow-x-auto lg:overflow-x-visible gap-1 pb-2 lg:pb-0 scrollbar-none">
                {[
                  { id: "preferences", label: "Career Preferences", icon: "🎯" },
                  { id: "education", label: "Education", icon: "🎓" },
                  { id: "skills", label: "Key Skills", icon: "⚡" },
                  { id: "languages", label: "Languages", icon: "🗣" },
                  { id: "internships", label: "Internships", icon: "💼" },
                  { id: "projects", label: "Projects", icon: "🚀" },
                  { id: "summary", label: "Profile Summary", icon: "📝" },
                  { id: "accomplishments", label: "Accomplishments", icon: "🏆" },
                  { id: "employment", label: "Employment", icon: "🏢" },
                  { id: "resume", label: "Resume", icon: "📄" },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => scrollToSection(item.id)}
                    className="whitespace-nowrap px-3 py-2 rounded-xl text-left font-medium text-slate-400 hover:text-white hover:bg-slate-900 transition-all flex items-center space-x-2 text-xs"
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Sections Column */}
            <div className="lg:col-span-3 space-y-6">
              {/* SECTION 1: Career Preferences */}
              <div id="preferences" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🎯</span>
                    <span>Career Preferences</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem(profile?.career_preferences || {});
                      setActiveModal("preferences");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    Edit
                  </button>
                </div>

                {profile?.career_preferences && Object.keys(profile.career_preferences).length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                    <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
                      <span className="text-slate-500 font-mono block mb-1">PREFERRED JOB TYPE</span>
                      <span className="text-white font-medium">
                        {profile.career_preferences.job_type || "Jobs, Internships"}
                      </span>
                    </div>
                    <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
                      <span className="text-slate-500 font-mono block mb-1">PREFERRED LOCATIONS</span>
                      <span className="text-white font-medium">
                        {profile.career_preferences.locations || "Bengaluru, Hyderabad, Remote"}
                      </span>
                    </div>
                    <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
                      <span className="text-slate-500 font-mono block mb-1">AVAILABILITY</span>
                      <span className="text-white font-medium">
                        {profile.career_preferences.availability || "Immediate / 15 Days"}
                      </span>
                    </div>
                    <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
                      <span className="text-slate-500 font-mono block mb-1">WORK MODE</span>
                      <span className="text-white font-medium">
                        {profile.career_preferences.work_mode || "Hybrid / Remote"}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No career preferences added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({});
                        setActiveModal("preferences");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add preferences
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 2: Education */}
              <div id="education" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🎓</span>
                    <span>Education</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ degree: "", institution: "", field: "", start_year: "", end_year: "", grade: "" });
                      setEditingIndex(null);
                      setActiveModal("education");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add
                  </button>
                </div>

                {profile?.education && profile.education.length > 0 ? (
                  <div className="space-y-3">
                    {profile.education.map((edu: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-white">{edu.degree || edu.degree_name || "Degree"}</h4>
                          <p className="text-xs text-sky-400 mt-0.5">{edu.institution || edu.school || "Institution"}</p>
                          <p className="text-[11px] text-slate-400 mt-1">
                            {edu.field && <span>{edu.field} • </span>}
                            <span>{edu.start_year || edu.start_date || "N/A"} - {edu.end_year || edu.end_date || "Present"}</span>
                            {edu.grade && <span className="ml-2 font-mono text-emerald-400">({edu.grade})</span>}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setEditingItem(edu);
                              setEditingIndex(idx);
                              setActiveModal("education");
                            }}
                            className="text-slate-400 hover:text-sky-400 text-xs"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => {
                              const updated = [...(profile.education || [])];
                              updated.splice(idx, 1);
                              saveProfileData({ education: updated }, "Education entry removed.");
                            }}
                            className="text-slate-500 hover:text-rose-400 text-xs"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No education added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ degree: "", institution: "", field: "", start_year: "", end_year: "", grade: "" });
                        setEditingIndex(null);
                        setActiveModal("education");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add education
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 3: Key Skills */}
              <div id="skills" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>⚡</span>
                    <span>Key Skills</span>
                  </h3>
                  <button
                    onClick={() => setActiveModal("skills")}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    Edit Skills
                  </button>
                </div>

                {profile?.skills && profile.skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {profile.skills.map((skill: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-sky-300 text-xs font-mono flex items-center space-x-1.5"
                      >
                        <span>{skill}</span>
                        <button
                          onClick={() => {
                            const updated = profile.skills?.filter((_, i) => i !== idx) || [];
                            saveProfileData({ skills: updated }, `Skill '${skill}' removed.`);
                          }}
                          className="text-slate-500 hover:text-rose-400 text-[10px]"
                        >
                          ✕
                        </button>
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No skills added yet.{" "}
                    <button onClick={() => setActiveModal("skills")} className="text-sky-400 underline font-normal">
                      Add skills
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 4: Languages */}
              <div id="languages" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🗣</span>
                    <span>Languages</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ language: "", proficiency: "Fluent" });
                      setEditingIndex(null);
                      setActiveModal("language");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add
                  </button>
                </div>

                {profile?.languages && profile.languages.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {profile.languages.map((lang: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800 flex justify-between items-center text-xs">
                        <div>
                          <span className="text-white font-bold block">{lang.language}</span>
                          <span className="text-slate-400 text-[11px] font-mono">{lang.proficiency || "Fluent"}</span>
                        </div>
                        <button
                          onClick={() => {
                            const updated = [...(profile.languages || [])];
                            updated.splice(idx, 1);
                            saveProfileData({ languages: updated }, "Language removed.");
                          }}
                          className="text-slate-500 hover:text-rose-400 text-xs"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No languages added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ language: "", proficiency: "Fluent" });
                        setEditingIndex(null);
                        setActiveModal("language");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add language
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 5: Internships */}
              <div id="internships" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>💼</span>
                    <span>Internships</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ organization: "", position: "", start_date: "", end_date: "", description: "" });
                      setEditingIndex(null);
                      setActiveModal("internship");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add
                  </button>
                </div>

                {profile?.internships && profile.internships.length > 0 ? (
                  <div className="space-y-3">
                    {profile.internships.map((intern: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-white">{intern.position}</h4>
                          <p className="text-xs text-sky-400 mt-0.5">{intern.organization}</p>
                          <p className="text-[11px] text-slate-400 mt-1">{intern.start_date} - {intern.end_date || "Present"}</p>
                          {intern.description && <p className="text-xs text-slate-300 mt-2">{intern.description}</p>}
                        </div>
                        <button
                          onClick={() => {
                            const updated = [...(profile.internships || [])];
                            updated.splice(idx, 1);
                            saveProfileData({ internships: updated }, "Internship removed.");
                          }}
                          className="text-slate-500 hover:text-rose-400 text-xs"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No internships added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ organization: "", position: "", start_date: "", end_date: "", description: "" });
                        setEditingIndex(null);
                        setActiveModal("internship");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add internship
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 6: Projects */}
              <div id="projects" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🚀</span>
                    <span>Projects</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ name: "", description: "", technologies: "", github_url: "", live_url: "" });
                      setEditingIndex(null);
                      setActiveModal("project");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add
                  </button>
                </div>

                {profile?.projects && profile.projects.length > 0 ? (
                  <div className="space-y-3">
                    {profile.projects.map((proj: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-white">{proj.name}</h4>
                          {proj.technologies && <p className="text-xs text-sky-400 font-mono mt-0.5">{proj.technologies}</p>}
                          {proj.description && <p className="text-xs text-slate-300 mt-2">{proj.description}</p>}
                          <div className="flex items-center space-x-4 mt-2 text-xs">
                            {proj.github_url && (
                              <a href={proj.github_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">
                                GitHub →
                              </a>
                            )}
                            {proj.live_url && (
                              <a href={proj.live_url} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
                                Live Demo →
                              </a>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            const updated = [...(profile.projects || [])];
                            updated.splice(idx, 1);
                            saveProfileData({ projects: updated }, "Project removed.");
                          }}
                          className="text-slate-500 hover:text-rose-400 text-xs"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No projects added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ name: "", description: "", technologies: "", github_url: "", live_url: "" });
                        setEditingIndex(null);
                        setActiveModal("project");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add project
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 7: Profile Summary */}
              <div id="summary" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>📝</span>
                    <span>Profile Summary</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ summary: profile?.summary || "" });
                      setActiveModal("summary");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    Edit
                  </button>
                </div>

                {profile?.summary ? (
                  <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-slate-800 whitespace-pre-wrap">
                    {profile.summary}
                  </p>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No summary added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ summary: "" });
                        setActiveModal("summary");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Write summary
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 8: Accomplishments */}
              <div id="accomplishments" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🏆</span>
                    <span>Accomplishments &amp; Certifications</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ title: "", issuer: "", year: "", description: "" });
                      setEditingIndex(null);
                      setActiveModal("accomplishment");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add
                  </button>
                </div>

                {profile?.accomplishments && Object.keys(profile.accomplishments).length > 0 ? (
                  <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 text-xs space-y-2">
                    <pre className="text-slate-300 font-mono whitespace-pre-wrap">
                      {JSON.stringify(profile.accomplishments, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No accomplishments or certifications added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ title: "", issuer: "", year: "", description: "" });
                        setEditingIndex(null);
                        setActiveModal("accomplishment");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add accomplishment
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 9: Employment */}
              <div id="employment" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🏢</span>
                    <span>Employment History</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ company: "", designation: "", start_date: "", end_date: "", description: "" });
                      setEditingIndex(null);
                      setActiveModal("employment");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add
                  </button>
                </div>

                {profile?.employment && profile.employment.length > 0 ? (
                  <div className="space-y-3">
                    {profile.employment.map((emp: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div>
                          <h4 className="text-sm font-bold text-white">{emp.designation}</h4>
                          <p className="text-xs text-sky-400 mt-0.5">{emp.company}</p>
                          <p className="text-[11px] text-slate-400 mt-1">{emp.start_date} - {emp.end_date || "Present"}</p>
                          {emp.description && <p className="text-xs text-slate-300 mt-2">{emp.description}</p>}
                        </div>
                        <button
                          onClick={() => {
                            const updated = [...(profile.employment || [])];
                            updated.splice(idx, 1);
                            saveProfileData({ employment: updated }, "Employment entry removed.");
                          }}
                          className="text-slate-500 hover:text-rose-400 text-xs"
                        >
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No employment records added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ company: "", designation: "", start_date: "", end_date: "", description: "" });
                        setEditingIndex(null);
                        setActiveModal("employment");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add employment
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 10: Resume */}
              <div id="resume" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>📄</span>
                    <span>Resume</span>
                  </h3>
                  <button
                    onClick={() => setActiveModal("resume")}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    Upload / Replace
                  </button>
                </div>

                {profile?.resume_filename || profile?.resume_url ? (
                  <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center text-lg font-bold">
                        📄
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-white">{profile.resume_filename || "resume.pdf"}</h4>
                        <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                          Uploaded: {profile.resume_updated_at || "Recently"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 text-xs">
                      {profile.resume_url && (
                        <a
                          href={profile.resume_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1.5 rounded-xl bg-sky-500 text-white font-bold hover:bg-sky-400 transition-all"
                        >
                          Download
                        </a>
                      )}
                      <button
                        onClick={() => setActiveModal("resume")}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 font-bold hover:bg-slate-700 transition-all"
                      >
                        Replace
                      </button>
                      <button
                        onClick={() => {
                          saveProfileData(
                            { resume_url: undefined, resume_filename: undefined, resume_updated_at: undefined },
                            "Resume deleted."
                          );
                        }}
                        className="px-3 py-1.5 rounded-xl bg-rose-500/10 text-rose-400 font-bold hover:bg-rose-500/20 border border-rose-500/30 transition-all"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No resume uploaded yet.{" "}
                    <button onClick={() => setActiveModal("resume")} className="text-sky-400 underline font-normal">
                      Upload resume (PDF)
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= MODALS ================= */}

      {/* Modal 1: Edit Profile Header */}
      {activeModal === "header" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Profile Header</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Headline</label>
                <input
                  type="text"
                  value={headerForm.headline}
                  onChange={(e) => setHeaderForm({ ...headerForm, headline: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Location</label>
                <input
                  type="text"
                  value={headerForm.location}
                  onChange={(e) => setHeaderForm({ ...headerForm, location: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Phone Number</label>
                <input
                  type="text"
                  value={headerForm.phone}
                  onChange={(e) => setHeaderForm({ ...headerForm, phone: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Degree</label>
                <input
                  type="text"
                  value={headerForm.degree}
                  onChange={(e) => setHeaderForm({ ...headerForm, degree: e.target.value })}
                  placeholder="e.g. B.Tech / B.E. Computer Science"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">College / University</label>
                <input
                  type="text"
                  value={headerForm.college}
                  onChange={(e) => setHeaderForm({ ...headerForm, college: e.target.value })}
                  placeholder="e.g. IIT Bhilai"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => saveProfileData(headerForm, "Profile header updated successfully.")}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 2: Edit Career Preferences */}
      {activeModal === "preferences" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Career Preferences</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Preferred Job Type</label>
                <input
                  type="text"
                  value={editingItem?.job_type || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, job_type: e.target.value })}
                  placeholder="e.g. Full-time Jobs, Internships"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Preferred Locations</label>
                <input
                  type="text"
                  value={editingItem?.locations || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, locations: e.target.value })}
                  placeholder="e.g. Bengaluru, Hyderabad, Remote"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Availability</label>
                <input
                  type="text"
                  value={editingItem?.availability || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, availability: e.target.value })}
                  placeholder="e.g. Immediate / 15 Days"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Work Mode</label>
                <input
                  type="text"
                  value={editingItem?.work_mode || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, work_mode: e.target.value })}
                  placeholder="e.g. Remote / Hybrid"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => saveProfileData({ career_preferences: editingItem }, "Career preferences saved.")}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Preferences"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Add / Edit Education */}
      {activeModal === "education" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">
              {editingIndex !== null ? "Edit Education" : "Add Education"}
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Degree / Certificate</label>
                <input
                  type="text"
                  value={editingItem?.degree || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, degree: e.target.value })}
                  placeholder="e.g. B.Tech / Class XII / Class X"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Institution / School</label>
                <input
                  type="text"
                  value={editingItem?.institution || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, institution: e.target.value })}
                  placeholder="e.g. Indian Institute of Technology (IIT), Bhilai"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Field of Study</label>
                <input
                  type="text"
                  value={editingItem?.field || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, field: e.target.value })}
                  placeholder="e.g. Computer Science & Engineering"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Start Year</label>
                  <input
                    type="text"
                    value={editingItem?.start_year || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, start_year: e.target.value })}
                    placeholder="e.g. 2022"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">End Year / Graduated</label>
                  <input
                    type="text"
                    value={editingItem?.end_year || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, end_year: e.target.value })}
                    placeholder="e.g. 2026"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Grade / CGPA / %</label>
                <input
                  type="text"
                  value={editingItem?.grade || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, grade: e.target.value })}
                  placeholder="e.g. 8.9 / 10"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const list = [...(profile?.education || [])];
                  if (editingIndex !== null) {
                    list[editingIndex] = editingItem;
                  } else {
                    list.push(editingItem);
                  }
                  saveProfileData({ education: list }, "Education updated.");
                }}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Education"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 4: Edit Skills */}
      {activeModal === "skills" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Manage Key Skills</h3>
            <p className="text-xs text-slate-400">Enter comma-separated skills (e.g. Python, React, FastAPI, SQL, RAG)</p>
            <textarea
              rows={4}
              value={editingItem?.skills_text ?? (profile?.skills?.join(", ") || "")}
              onChange={(e) => setEditingItem({ skills_text: e.target.value })}
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
            />
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const str = editingItem?.skills_text ?? (profile?.skills?.join(", ") || "");
                  const skillList = str
                    .split(",")
                    .map((s: string) => s.trim())
                    .filter((s: string) => s.length > 0);
                  saveProfileData({ skills: skillList }, "Key skills updated.");
                }}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Skills"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 5: Edit Profile Summary */}
      {activeModal === "summary" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Profile Summary</h3>
            <textarea
              rows={5}
              value={editingItem?.summary ?? ""}
              onChange={(e) => setEditingItem({ summary: e.target.value })}
              placeholder="Write a brief professional summary of your background, experience, and career objectives..."
              className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
            />
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => saveProfileData({ summary: editingItem?.summary }, "Summary updated.")}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Summary"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 6: Add / Edit Internship */}
      {activeModal === "internship" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Internship</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Organization / Company</label>
                <input
                  type="text"
                  value={editingItem?.organization || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, organization: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Position / Role</label>
                <input
                  type="text"
                  value={editingItem?.position || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, position: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Start Date</label>
                  <input
                    type="text"
                    value={editingItem?.start_date || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, start_date: e.target.value })}
                    placeholder="e.g. May 2024"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">End Date</label>
                  <input
                    type="text"
                    value={editingItem?.end_date || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, end_date: e.target.value })}
                    placeholder="e.g. Aug 2024"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editingItem?.description || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const list = [...(profile?.internships || [])];
                  list.push(editingItem);
                  saveProfileData({ internships: list }, "Internship added.");
                }}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Internship"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 7: Add / Edit Project */}
      {activeModal === "project" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Project</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Project Name</label>
                <input
                  type="text"
                  value={editingItem?.name || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, name: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Technologies Used</label>
                <input
                  type="text"
                  value={editingItem?.technologies || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, technologies: e.target.value })}
                  placeholder="e.g. Next.js, Python, PostgreSQL, Vector Search"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editingItem?.description || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-mono mb-1">GitHub URL</label>
                  <input
                    type="text"
                    value={editingItem?.github_url || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, github_url: e.target.value })}
                    placeholder="https://github.com/..."
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">Live URL</label>
                  <input
                    type="text"
                    value={editingItem?.live_url || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, live_url: e.target.value })}
                    placeholder="https://..."
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const list = [...(profile?.projects || [])];
                  list.push(editingItem);
                  saveProfileData({ projects: list }, "Project added.");
                }}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Project"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 8: Upload / Replace Resume */}
      {activeModal === "resume" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Upload Resume</h3>
            <p className="text-xs text-slate-400">Select a PDF or DOCX file (Max size 10MB)</p>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  const now = new Date().toLocaleDateString();
                  saveProfileData(
                    {
                      resume_filename: file.name,
                      resume_url: `/uploads/resumes/${file.name}`,
                      resume_filesize: file.size,
                      resume_updated_at: now,
                    },
                    "Resume uploaded successfully."
                  );
                }
              }}
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-sky-500 file:text-white hover:file:bg-sky-400 cursor-pointer"
            />
            <div className="flex justify-end pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
