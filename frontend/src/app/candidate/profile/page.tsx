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
  | "summary"
  | "experience"
  | "education"
  | "skills"
  | "languages"
  | "projects"
  | "accomplishments"
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
    full_name: "",
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
            full_name: (data as any).full_name || user?.full_name || "",
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
  }, [user]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  // Helper to calculate profile completion percentage
  const calculateCompletion = (p: CandidateProfileData | null): number => {
    if (!p) return 0;
    let score = 0;
    let total = 7;

    const displayName = (p as any).full_name || user?.full_name;
    if (displayName && user?.email) score++;
    if (p.headline || p.location || p.phone) score++;
    if (p.summary && p.summary.trim().length > 10) score++;
    if (p.career_preferences && Object.keys(p.career_preferences).length > 0) score++;
    if (p.degree || p.college || (p.education && p.education.length > 0)) score++;
    if (p.skills && p.skills.length > 0) score++;
    if (p.resume_url || p.resume_filename) score++;

    return Math.round((score / total) * 100);
  };

  const saveProfileData = async (updatedFields: Partial<CandidateProfileData>, toastMsg: string) => {
    setSaving(true);
    setError(null);
    try {
      const result = await updateCandidateProfile(updatedFields);
      setProfile((prev) => ({ ...prev, ...result }));
      showToast(toastMsg);
      setActiveModal(null);
      setEditingItem(null);
      setEditingIndex(null);

      // Trigger Navbar refresh for instant photo/name update
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("candidate_profile_updated"));
      }
    } catch (err: any) {
      setError(err.message || "Failed to save changes.");
    } finally {
      setSaving(false);
    }
  };

  // Photo upload handler with Canvas avatar resizing for crisp display & fast saving
  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      setError("Image size should be less than 10MB.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const size = 300; // 300x300 avatar resolution
        canvas.width = size;
        canvas.height = size;

        if (ctx) {
          // Center crop to square avatar
          const minSide = Math.min(img.width, img.height);
          const sx = (img.width - minSide) / 2;
          const sy = (img.height - minSide) / 2;
          ctx.drawImage(img, sx, sy, minSide, minSide, 0, 0, size, size);
          const resizedDataUrl = canvas.toDataURL("image/jpeg", 0.85);
          setHeaderForm((prev) => ({ ...prev, photo_url: resizedDataUrl }));
        } else {
          setHeaderForm((prev) => ({ ...prev, photo_url: event.target?.result as string }));
        }
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
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
  const currentName = (profile as any)?.full_name || user?.full_name || "Candidate Name";

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
                  <span>{currentName.charAt(0).toUpperCase()}</span>
                )}
              </div>
            </div>

            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-2xl font-black text-white">{currentName}</h2>
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
                  onClick={() => {
                    setHeaderForm({
                      full_name: currentName,
                      headline: profile?.headline || "",
                      location: profile?.location || "",
                      phone: profile?.phone || "",
                      degree: profile?.degree || "",
                      college: profile?.college || "",
                      photo_url: profile?.photo_url || "",
                    });
                    setActiveModal("header");
                  }}
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
                  { id: "summary", label: "Profile Summary", icon: "📝" },
                  { id: "experience", label: "Experience", icon: "💼" },
                  { id: "education", label: "Education", icon: "🎓" },
                  { id: "skills", label: "Key Skills", icon: "⚡" },
                  { id: "languages", label: "Languages", icon: "🗣" },
                  { id: "projects", label: "Projects", icon: "🚀" },
                  { id: "accomplishments", label: "Accomplishments", icon: "🏆" },
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
              {/* SECTION 1: Profile Summary (TOP SUMMARY) */}
              <div id="summary" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>📝</span>
                    <span>Profile Summary</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem(profile?.summary || "");
                      setActiveModal("summary");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    Edit
                  </button>
                </div>

                {profile?.summary ? (
                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {profile.summary}
                  </p>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No profile summary added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem("");
                        setActiveModal("summary");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add summary
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 2: Experience (Work / Past Experience Records) */}
              <div id="experience" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>💼</span>
                    <span>Experience</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ designation: "", company: "", start_date: "", end_date: "Present", description: "" });
                      setEditingIndex(null);
                      setActiveModal("experience");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add Experience
                  </button>
                </div>

                {profile?.experience && profile.experience.length > 0 ? (
                  <div className="space-y-3">
                    {profile.experience.map((exp: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div className="space-y-1">
                          <h4 className="text-sm font-bold text-white">{exp.designation || exp.title}</h4>
                          <p className="text-xs font-semibold text-sky-400">{exp.company}</p>
                          <p className="text-[11px] font-mono text-slate-400">
                            {exp.start_date} {exp.end_date ? `– ${exp.end_date}` : "– Present"}
                          </p>
                          {exp.description && (
                            <p className="text-xs text-slate-300 leading-relaxed pt-1.5 whitespace-pre-wrap">
                              {exp.description}
                            </p>
                          )}
                          {(exp.skills_used || exp.skills) && (
                            <div className="flex flex-wrap gap-1.5 pt-2">
                              {(typeof (exp.skills_used || exp.skills) === "string"
                                ? (exp.skills_used || exp.skills).split(",")
                                : exp.skills_used || exp.skills
                              ).map((sk: string, sIdx: number) => {
                                const clean = sk.trim();
                                if (!clean) return null;
                                return (
                                  <span
                                    key={sIdx}
                                    className="px-2.5 py-0.5 rounded-lg bg-sky-950/60 border border-sky-800/80 text-sky-300 text-[10px] font-semibold"
                                  >
                                    ★ {clean}
                                  </span>
                                );
                              })}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 shrink-0 ml-4">
                          <button
                            onClick={() => {
                              setEditingItem({
                                ...exp,
                                designation: exp.designation || exp.title || "",
                                company: exp.company || "",
                                start_date: exp.start_date || "",
                                end_date: exp.end_date || "Present",
                                description: exp.description || "",
                                skills_used: exp.skills_used || exp.skills || "",
                              });
                              setEditingIndex(idx);
                              setActiveModal("experience");
                            }}
                            className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                          >
                            ✏ Edit
                          </button>
                          <button
                            onClick={() => {
                              const updated = [...(profile.experience || [])];
                              updated.splice(idx, 1);
                              saveProfileData({ experience: updated }, "Experience entry removed.");
                            }}
                            className="text-slate-500 hover:text-rose-400 text-xs font-bold"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No work experience added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ designation: "", company: "", start_date: "", end_date: "Present", description: "" });
                        setEditingIndex(null);
                        setActiveModal("experience");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add experience
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 3: Education */}
              <div id="education" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🎓</span>
                    <span>Education</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ degree: "", department: "", institution: "", location: "", start_year: "", end_year: "", year: "", percentage: "", grade: "" });
                      setEditingIndex(null);
                      setActiveModal("education");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add Education
                  </button>
                </div>

                {profile?.education && profile.education.length > 0 ? (
                  <div className="space-y-3">
                    {profile.education.map((edu: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div className="space-y-1">
                          <h4 className="text-sm font-bold text-white">
                            {edu.degree} {edu.department ? `— ${edu.department}` : ""}
                          </h4>
                          <p className="text-xs font-semibold text-sky-400">
                            {edu.institution || edu.college} {edu.location ? `(${edu.location})` : ""}
                          </p>
                          <p className="text-[11px] font-mono text-slate-400">
                            {edu.start_year ? `${edu.start_year} – ${edu.end_year || edu.year}` : `Passing Year: ${edu.year || edu.end_year}`}
                            {(edu.percentage || edu.grade) && ` | Score: ${edu.percentage || edu.grade}`}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2 shrink-0 ml-4">
                          <button
                            onClick={() => {
                              setEditingItem({
                                ...edu,
                                degree: edu.degree || "",
                                department: edu.department || "",
                                institution: edu.institution || edu.college || "",
                                location: edu.location || "",
                                start_year: edu.start_year || "",
                                end_year: edu.end_year || edu.year || "",
                                year: edu.year || edu.end_year || "",
                                percentage: edu.percentage || edu.grade || "",
                              });
                              setEditingIndex(idx);
                              setActiveModal("education");
                            }}
                            className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                          >
                            ✏ Edit
                          </button>
                          <button
                            onClick={() => {
                              const updated = [...(profile.education || [])];
                              updated.splice(idx, 1);
                              saveProfileData({ education: updated }, "Education entry removed.");
                            }}
                            className="text-slate-500 hover:text-rose-400 text-xs font-bold"
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
                        setEditingItem({ degree: "", department: "", institution: "", location: "", start_year: "", end_year: "", year: "", percentage: "", grade: "" });
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

              {/* SECTION 4: Key Skills */}
              <div id="skills" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>⚡</span>
                    <span>Key Skills</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem((profile?.skills || []).join(", "));
                      setActiveModal("skills");
                    }}
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
                        className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-sky-400 text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No skills added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem("");
                        setActiveModal("skills");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add skills
                    </button>
                  </div>
                )}
              </div>

              {/* SECTION 5: Languages */}
              <div id="languages" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🗣</span>
                    <span>Languages</span>
                  </h3>
                  <button
                    onClick={() => {
                      setEditingItem({ name: "", proficiency: "Full Professional" });
                      setEditingIndex(null);
                      setActiveModal("languages");
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
                          <span className="font-bold text-white">{lang.name}</span>
                          <span className="text-slate-400 block text-[11px]">{lang.proficiency}</span>
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
                        setEditingItem({ name: "", proficiency: "Full Professional" });
                        setEditingIndex(null);
                        setActiveModal("languages");
                      }}
                      className="text-sky-400 underline font-normal"
                    >
                      Add language
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
                      setEditingItem({ title: "", description: "", link: "", tech_stack: "" });
                      setEditingIndex(null);
                      setActiveModal("project");
                    }}
                    className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    + Add Project
                  </button>
                </div>

                {profile?.projects && profile.projects.length > 0 ? (
                  <div className="space-y-3">
                    {profile.projects.map((proj: any, idx: number) => (
                      <div key={idx} className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 flex justify-between items-start">
                        <div className="space-y-1">
                          <h4 className="text-sm font-bold text-white">{proj.title}</h4>
                          {proj.link && (
                            <a href={proj.link} target="_blank" rel="noreferrer" className="text-xs text-sky-400 underline inline-block">
                              {proj.link}
                            </a>
                          )}
                          {proj.description && <p className="text-xs text-slate-300 leading-relaxed pt-1 whitespace-pre-wrap">{proj.description}</p>}
                          {(proj.tech_stack || proj.skills_used || proj.skills) && (
                            <div className="flex flex-wrap gap-1.5 pt-2">
                              {(typeof (proj.tech_stack || proj.skills_used || proj.skills) === "string"
                                ? (proj.tech_stack || proj.skills_used || proj.skills).split(",")
                                : proj.tech_stack || proj.skills_used || proj.skills
                              ).map((sk: string, sIdx: number) => {
                                const clean = sk.trim();
                                if (!clean) return null;
                                return (
                                  <span
                                    key={sIdx}
                                    className="px-2.5 py-0.5 rounded-lg bg-sky-950/60 border border-sky-800/80 text-sky-300 text-[10px] font-semibold"
                                  >
                                    ★ {clean}
                                  </span>
                                );
                              })}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2 shrink-0 ml-4">
                          <button
                            onClick={() => {
                              setEditingItem({
                                ...proj,
                                title: proj.title || "",
                                link: proj.link || "",
                                description: proj.description || "",
                                tech_stack: proj.tech_stack || proj.skills_used || proj.skills || "",
                              });
                              setEditingIndex(idx);
                              setActiveModal("project");
                            }}
                            className="text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline"
                          >
                            ✏ Edit
                          </button>
                          <button
                            onClick={() => {
                              const updated = [...(profile.projects || [])];
                              updated.splice(idx, 1);
                              saveProfileData({ projects: updated }, "Project removed.");
                            }}
                            className="text-slate-500 hover:text-rose-400 text-xs font-bold"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No projects added yet.{" "}
                    <button
                      onClick={() => {
                        setEditingItem({ title: "", description: "", link: "", tech_stack: "" });
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

              {/* SECTION 7: Accomplishments */}
              <div id="accomplishments" className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>🏆</span>
                    <span>Accomplishments</span>
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
                  <div className="bg-slate-900/60 p-4 rounded-2xl border border-slate-800 space-y-2 text-xs">
                    {Object.entries(profile.accomplishments).map(([k, v]: [string, any], idx: number) => (
                      <div key={idx} className="flex justify-between items-center border-b border-slate-800/50 pb-1.5 last:border-0 last:pb-0">
                        <span className="text-slate-400 font-mono capitalize">{k}:</span>
                        <span className="text-white font-medium">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs italic py-2">
                    No accomplishments added yet.{" "}
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

              {/* SECTION 8: Resume */}
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

      {/* ================= MODALS ================= */}

      {/* Modal 1: Edit Profile Header */}
      {activeModal === "header" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Profile Header</h3>

            {/* Live Photo Preview */}
            <div className="flex items-center space-x-4 bg-slate-900/80 p-3 rounded-2xl border border-slate-800">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white font-black text-xl flex items-center justify-center border border-slate-700 overflow-hidden shrink-0">
                {headerForm.photo_url ? (
                  <img src={headerForm.photo_url} alt="Preview" className="w-full h-full object-cover" />
                ) : (
                  <span>{headerForm.full_name?.charAt(0).toUpperCase() || "C"}</span>
                )}
              </div>
              <div className="space-y-1 text-xs flex-1">
                <label htmlFor="cand-photo-input" className="block text-slate-300 font-semibold">Upload Candidate Photo</label>
                <input
                  id="cand-photo-input"
                  name="candidatePhoto"
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoUpload}
                  className="block w-full text-[11px] text-slate-400 file:mr-3 file:py-1 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-sky-500 file:text-white hover:file:bg-sky-400 cursor-pointer"
                />
              </div>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label htmlFor="cand-prof-full-name-input" className="block text-slate-400 font-mono mb-1">Candidate Full Name</label>
                <input
                  id="cand-prof-full-name-input"
                  name="fullName"
                  autoComplete="name"
                  type="text"
                  value={headerForm.full_name}
                  onChange={(e) => setHeaderForm({ ...headerForm, full_name: e.target.value })}
                  placeholder="Enter your full name"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label htmlFor="cand-prof-headline-input" className="block text-slate-400 font-mono mb-1">Headline</label>
                <input
                  id="cand-prof-headline-input"
                  name="headline"
                  type="text"
                  value={headerForm.headline}
                  onChange={(e) => setHeaderForm({ ...headerForm, headline: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label htmlFor="cand-prof-location-input" className="block text-slate-400 font-mono mb-1">Location</label>
                <input
                  id="cand-prof-location-input"
                  name="location"
                  type="text"
                  value={headerForm.location}
                  onChange={(e) => setHeaderForm({ ...headerForm, location: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label htmlFor="cand-prof-phone-input" className="block text-slate-400 font-mono mb-1">Phone Number</label>
                <input
                  id="cand-prof-phone-input"
                  name="phone"
                  autoComplete="tel"
                  type="text"
                  value={headerForm.phone}
                  onChange={(e) => setHeaderForm({ ...headerForm, phone: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label htmlFor="cand-prof-degree-input" className="block text-slate-400 font-mono mb-1">Degree</label>
                <input
                  id="cand-prof-degree-input"
                  name="degree"
                  type="text"
                  value={headerForm.degree}
                  onChange={(e) => setHeaderForm({ ...headerForm, degree: e.target.value })}
                  placeholder="e.g. B.Tech / B.E. Computer Science"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label htmlFor="cand-prof-college-input" className="block text-slate-400 font-mono mb-1">College / University</label>
                <input
                  id="cand-prof-college-input"
                  name="college"
                  autoComplete="organization"
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
                {saving ? "Saving..." : "Save Header"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 2: Add Work Experience */}
      {activeModal === "experience" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">
              {editingIndex !== null ? "Edit Work Experience" : "Add Work Experience"}
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Job Title / Designation</label>
                <input
                  type="text"
                  value={editingItem?.designation || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, designation: e.target.value })}
                  placeholder="e.g. Senior Software Engineer / AI Developer"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Company Name</label>
                <input
                  type="text"
                  value={editingItem?.company || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, company: e.target.value })}
                  placeholder="e.g. OneHaul Logistics / Tech Corp"
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
                    placeholder="e.g. Jan 2024"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono mb-1">End Date</label>
                  <input
                    type="text"
                    value={editingItem?.end_date || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, end_date: e.target.value })}
                    placeholder="e.g. Present or Dec 2025"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Role Description &amp; Key Achievements</label>
                <textarea
                  rows={4}
                  value={editingItem?.description || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  placeholder="Describe your core responsibilities, projects handled, and achievements..."
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Key Skills &amp; Technologies Used</label>
                <input
                  type="text"
                  value={editingItem?.skills_used || editingItem?.skills || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, skills_used: e.target.value })}
                  placeholder="e.g. Python, FastAPI, RAG, PostgreSQL, Docker"
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
                  const updated = [...(profile?.experience || [])];
                  if (editingIndex !== null && editingIndex >= 0) {
                    updated[editingIndex] = editingItem;
                  } else {
                    updated.push(editingItem);
                  }
                  saveProfileData(
                    { experience: updated },
                    editingIndex !== null ? "Work experience updated successfully." : "Work experience added successfully."
                  );
                }}
                disabled={saving || !editingItem?.designation || !editingItem?.company}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Experience"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 3: Edit Summary */}
      {activeModal === "summary" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Profile Summary</h3>
            <div>
              <textarea
                rows={5}
                value={editingItem}
                onChange={(e) => setEditingItem(e.target.value)}
                placeholder="Write a concise overview of your career background, expertise, and goals..."
                className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
              />
            </div>
            <div className="flex justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() => saveProfileData({ summary: editingItem }, "Profile summary updated.")}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Summary"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 4: Add / Edit Education */}
      {activeModal === "education" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">
              {editingIndex !== null ? "Edit Education" : "Add Education"}
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Degree / Qualification</label>
                <input
                  type="text"
                  value={editingItem?.degree || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, degree: e.target.value })}
                  placeholder="e.g. B.Tech / B.E. / M.Tech"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Department / Specialization</label>
                <input
                  type="text"
                  value={editingItem?.department || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, department: e.target.value })}
                  placeholder="e.g. Computer Science & Engineering"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Institution / College</label>
                <input
                  type="text"
                  value={editingItem?.institution || editingItem?.college || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, institution: e.target.value, college: e.target.value })}
                  placeholder="e.g. IIT Bhilai"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">College Address / Location</label>
                <input
                  type="text"
                  value={editingItem?.location || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, location: e.target.value })}
                  placeholder="e.g. Bhilai, Chhattisgarh"
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
                  <label className="block text-slate-400 font-mono mb-1">End Year / Passing Year</label>
                  <input
                    type="text"
                    value={editingItem?.end_year || editingItem?.year || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, end_year: e.target.value, year: e.target.value })}
                    placeholder="e.g. 2026"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Percentage / CGPA</label>
                <input
                  type="text"
                  value={editingItem?.percentage || editingItem?.grade || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, percentage: e.target.value, grade: e.target.value })}
                  placeholder="e.g. 85% or 8.5 CGPA"
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
                  const updated = [...(profile?.education || [])];
                  if (editingIndex !== null && editingIndex >= 0) {
                    updated[editingIndex] = editingItem;
                  } else {
                    updated.push(editingItem);
                  }
                  saveProfileData(
                    { education: updated },
                    editingIndex !== null ? "Education entry updated successfully." : "Education entry added successfully."
                  );
                }}
                disabled={saving || !editingItem?.degree}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Education"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 5: Edit Skills */}
      {activeModal === "skills" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Edit Key Skills</h3>
            <div>
              <label className="block text-slate-400 font-mono mb-1">Comma Separated Skills</label>
              <textarea
                rows={3}
                value={editingItem}
                onChange={(e) => setEditingItem(e.target.value)}
                placeholder="Python, FastAPI, RAG, Machine Learning, PostgreSQL"
                className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
              />
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
                  const parsed = editingItem
                    .split(",")
                    .map((s: string) => s.trim())
                    .filter(Boolean);
                  saveProfileData({ skills: parsed }, "Key skills updated.");
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

      {/* Modal 6: Edit Languages */}
      {activeModal === "languages" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Language</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Language Name</label>
                <input
                  type="text"
                  value={editingItem?.name || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, name: e.target.value })}
                  placeholder="e.g. English, Telugu, Hindi"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Proficiency Level</label>
                <select
                  value={editingItem?.proficiency || "Full Professional"}
                  onChange={(e) => setEditingItem({ ...editingItem, proficiency: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                >
                  <option value="Native / Bilingual">Native / Bilingual</option>
                  <option value="Full Professional">Full Professional</option>
                  <option value="Professional Working">Professional Working</option>
                  <option value="Elementary">Elementary</option>
                </select>
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
                  const updated = [...(profile?.languages || []), editingItem];
                  saveProfileData({ languages: updated }, "Language added.");
                }}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Language"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 7: Add / Edit Project */}
      {activeModal === "project" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">
              {editingIndex !== null ? "Edit Project" : "Add Project"}
            </h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Project Title</label>
                <input
                  type="text"
                  value={editingItem?.title || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, title: e.target.value })}
                  placeholder="e.g. AI Hiring System & Talent OS"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Project Link (Optional)</label>
                <input
                  type="text"
                  value={editingItem?.link || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, link: e.target.value })}
                  placeholder="https://github.com/..."
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Description</label>
                <textarea
                  rows={3}
                  value={editingItem?.description || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  placeholder="Describe your project, core features, and key outcomes..."
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Technologies &amp; Skills Used</label>
                <input
                  type="text"
                  value={editingItem?.tech_stack || editingItem?.skills_used || editingItem?.skills || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, tech_stack: e.target.value })}
                  placeholder="e.g. React, Next.js, Python, FastAPI, PostgreSQL, Docker"
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
                  const updated = [...(profile?.projects || [])];
                  if (editingIndex !== null && editingIndex >= 0) {
                    updated[editingIndex] = editingItem;
                  } else {
                    updated.push(editingItem);
                  }
                  saveProfileData(
                    { projects: updated },
                    editingIndex !== null ? "Project entry updated successfully." : "Project entry added successfully."
                  );
                }}
                disabled={saving || !editingItem?.title}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Project"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 8: Edit Accomplishment */}
      {activeModal === "accomplishment" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Add Accomplishment</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Title / Certificate</label>
                <input
                  type="text"
                  value={editingItem?.title || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, title: e.target.value })}
                  placeholder="e.g. AWS Certified Solutions Architect"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white font-mono text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-400 font-mono mb-1">Issuing Authority</label>
                <input
                  type="text"
                  value={editingItem?.issuer || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, issuer: e.target.value })}
                  placeholder="e.g. Amazon Web Services"
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
                  const existingAcc = profile?.accomplishments || {};
                  const updated = { ...existingAcc, [editingItem.title || "certification"]: editingItem.issuer };
                  saveProfileData({ accomplishments: updated }, "Accomplishment added.");
                }}
                disabled={saving}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Saving..." : "Save Accomplishment"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal 9: Upload Resume */}
      {activeModal === "resume" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-800 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Upload Candidate Resume</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono mb-1">Select Resume File (PDF / DOCX)</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.doc"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setEditingItem({
                        filename: file.name,
                        filesize: file.size,
                        url: `/uploads/resumes/${file.name}`,
                      });
                    }
                  }}
                  className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-sky-500 file:text-white hover:file:bg-sky-400 cursor-pointer"
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
                  if (editingItem?.filename) {
                    saveProfileData(
                      {
                        resume_filename: editingItem.filename,
                        resume_url: editingItem.url,
                        resume_updated_at: new Date().toISOString().split("T")[0],
                      },
                      "Resume uploaded successfully."
                    );
                  }
                }}
                disabled={saving || !editingItem?.filename}
                className="px-4 py-2 rounded-xl bg-sky-500 text-white text-xs font-bold hover:bg-sky-400 disabled:opacity-50"
              >
                {saving ? "Uploading..." : "Save Resume"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
