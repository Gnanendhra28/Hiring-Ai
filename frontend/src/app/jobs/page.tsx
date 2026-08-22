"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  BriefcaseBusiness,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FilterX,
  MapPin,
  Plus,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

const PRESET_LOCATIONS = [
  "Bengaluru",
  "Pune",
  "Remote",
  "Hyderabad",
  "Mumbai",
  "Delhi NCR",
  "Chennai",
];

const PRESET_WORK_TYPES = ["On-site", "Remote", "Hybrid"];

const PRESET_EXPERIENCE_RANGES = [
  "0–1 Years (Entry Level)",
  "1–3 Years (Junior)",
  "3–5 Years (Mid Level)",
  "5–8 Years (Senior)",
  "8–12 Years (Lead/Staff)",
  "12–15+ Years (Executive/Principal)",
];

const PRESET_SKILLS = [
  "Python",
  "Machine Learning",
  "Generative AI",
  "FastAPI",
  "RAG",
  "Docker",
  "SQL",
  "PostgreSQL",
  "LLMs",
  "PyTorch",
  "React",
  "TypeScript",
];

const PAGE_SIZE = 10;

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Pagination State (15 jobs per page)
  const [currentPage, setCurrentPage] = useState(1);

  // Filters State
  const [selectedLocations, setSelectedLocations] = useState<string[]>([]);
  const [locationSearch, setLocationSearch] = useState("");
  const [customLocationInput, setCustomLocationInput] = useState("");
  const [showLocationPopover, setShowLocationPopover] = useState(false);

  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [showTypePopover, setShowTypePopover] = useState(false);

  const [selectedExperience, setSelectedExperience] = useState<string[]>([]);
  const [showExpPopover, setShowExpPopover] = useState(false);

  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [skillSearch, setSkillSearch] = useState("");
  const [customSkillInput, setCustomSkillInput] = useState("");
  const [showSkillPopover, setShowSkillPopover] = useState(false);

  const filterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  // Close filter popovers on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setShowLocationPopover(false);
        setShowTypePopover(false);
        setShowExpPopover(false);
        setShowSkillPopover(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Reset page to 1 whenever filters or search query change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedLocations, selectedTypes, selectedExperience, selectedSkills]);

function getTimeAgo(dateInput?: string | Date) {
  if (!dateInput) return "Recently";
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return "Recently";

  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
  if (seconds < 60) return "Just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days > 1 ? "s" : ""} ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months > 1 ? "s" : ""} ago`;
  const years = Math.floor(days / 365);
  return `${years} year${years > 1 ? "s" : ""} ago`;
}

  useEffect(() => {
    async function loadJobs() {
      try {
        const res = await apiFetch("/api/v1/jobs");
        if (res.ok) {
          const data = await res.json();
          const apiItems = data.items || [];

          const formattedRealJobs = apiItems.map((j: any) => ({
            id: j.slug || j.id,
            title: j.title,
            company: j.department || "Enterprise Requisition",
            location: j.location || "Remote",
            employment_type: j.employment_type || "FULL_TIME",
            work_mode: j.location?.toLowerCase().includes("remote")
              ? "Remote"
              : j.location?.toLowerCase().includes("hybrid")
              ? "Hybrid"
              : "On-site",
            experience: "3–5 Years (Mid Level)",
            status: j.status,
            salary: j.salary,
            company_website: j.company_website,
            posted: getTimeAgo(j.created_at),
            description: j.description,
          }));

          setJobs(formattedRealJobs);
        }
      } catch (err) {
        console.error("Error loading jobs:", err);
      } finally {
        setLoading(false);
      }
    }
    loadJobs();
  }, []);

  // Filter Handlers
  const toggleLocation = (loc: string) => {
    setSelectedLocations((prev) =>
      prev.includes(loc) ? prev.filter((l) => l !== loc) : [...prev, loc]
    );
  };

  const addCustomLocation = () => {
    if (customLocationInput.trim() && !selectedLocations.includes(customLocationInput.trim())) {
      setSelectedLocations([...selectedLocations, customLocationInput.trim()]);
      setCustomLocationInput("");
    }
  };

  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const toggleExperience = (exp: string) => {
    setSelectedExperience((prev) =>
      prev.includes(exp) ? prev.filter((e) => e !== exp) : [...prev, exp]
    );
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const addCustomSkill = () => {
    if (customSkillInput.trim() && !selectedSkills.includes(customSkillInput.trim())) {
      setSelectedSkills([...selectedSkills, customSkillInput.trim()]);
      setCustomSkillInput("");
    }
  };

  const clearAllFilters = () => {
    setSelectedLocations([]);
    setSelectedTypes([]);
    setSelectedExperience([]);
    setSelectedSkills([]);
    setSearchQuery("");
    setLocationSearch("");
    setSkillSearch("");
  };

  const hasActiveFilters =
    selectedLocations.length > 0 ||
    selectedTypes.length > 0 ||
    selectedExperience.length > 0 ||
    selectedSkills.length > 0 ||
    searchQuery.trim().length > 0;

  // Filter Jobs logic
  const filteredJobs = jobs.filter((j) => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = j.title.toLowerCase().includes(q);
      const matchDept = j.company.toLowerCase().includes(q);
      const matchLoc = j.location.toLowerCase().includes(q);
      const matchSkills = j.skills.some((s: string) => s.toLowerCase().includes(q));
      if (!matchTitle && !matchDept && !matchLoc && !matchSkills) return false;
    }

    if (selectedLocations.length > 0) {
      const matchLoc = selectedLocations.some((loc) =>
        j.location.toLowerCase().includes(loc.toLowerCase())
      );
      if (!matchLoc) return false;
    }

    if (selectedTypes.length > 0) {
      const matchType = selectedTypes.some(
        (t) =>
          j.work_mode.toLowerCase() === t.toLowerCase() ||
          j.location.toLowerCase().includes(t.toLowerCase())
      );
      if (!matchType) return false;
    }

    if (selectedExperience.length > 0) {
      const matchExp = selectedExperience.some((exp) =>
        j.experience.includes(exp.split(" ")[0])
      );
      if (!matchExp) return false;
    }

    if (selectedSkills.length > 0) {
      const matchSkill = selectedSkills.some((s) =>
        j.skills.some((js: string) => js.toLowerCase() === s.toLowerCase())
      );
      if (!matchSkill) return false;
    }

    return true;
  });

  // Calculate 15 Jobs Per Page Pagination
  const totalFiltered = filteredJobs.length;
  const totalPages = Math.ceil(totalFiltered / PAGE_SIZE) || 1;
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const endIndex = Math.min(startIndex + PAGE_SIZE, totalFiltered);
  const paginatedJobs = filteredJobs.slice(startIndex, endIndex);

  return (
    <div className="h-page space-y-6 text-slate-100">
      {/* Header Title Banner */}
      <section className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow text-indigo-400">Job Requisitions</p>
          <h1 className="page-title text-white">Explore Verified Positions</h1>
          <p className="page-subtitle text-slate-300">
            AI-matched job openings aligned with your skills, location, and career experience.
          </p>
        </div>
      </section>

      {/* Search Bar */}
      <section className="h-card ai-card p-6 sm:p-8 relative overflow-hidden bg-slate-900 border-slate-800">
        <div className="space-y-2">
          <span className="inline-block px-3 py-1 rounded-lg bg-indigo-900 text-indigo-200 text-xs font-extrabold uppercase tracking-wider">
            AI Smart Search
          </span>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white mt-1">
            Find your next opportunity with AI
          </h2>
          <p className="text-xs sm:text-sm text-slate-300">
            Search open roles by technology stack, title, location type, or target department.
          </p>
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <label className="flex flex-1 items-center gap-3 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 shadow-xs">
            <Sparkles size={18} className="text-indigo-400 shrink-0" />
            <input
              className="w-full border-0 bg-transparent text-xs sm:text-sm text-white placeholder-slate-400 outline-none"
              placeholder="Search jobs by title, department, skills, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery("")} className="text-slate-400 hover:text-white">
                <X size={15} />
              </button>
            )}
          </label>
          <button className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 transition-all">
            <Search size={16} /> Search Jobs
          </button>
        </div>
      </section>

      {/* Interactive Filter Bar */}
      <div className="relative" ref={filterRef}>
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Location Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowLocationPopover(!showLocationPopover);
                setShowTypePopover(false);
                setShowExpPopover(false);
                setShowSkillPopover(false);
              }}
              className={`px-3.5 py-2 rounded-xl border text-xs font-semibold flex items-center gap-2 transition-all shadow-xs ${
                selectedLocations.length > 0
                  ? "bg-indigo-600 text-white border-indigo-500 shadow-indigo-600/20"
                  : "bg-slate-900 border-slate-800 text-slate-200 hover:border-slate-700"
              }`}
            >
              <MapPin size={14} className="text-indigo-400" />
              <span>
                {selectedLocations.length > 0
                  ? `Location (${selectedLocations.length})`
                  : "Location"}
              </span>
              <ChevronDown size={14} />
            </button>

            {showLocationPopover && (
              <div className="absolute left-0 top-12 w-72 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-3 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-white text-xs">Filter by Location</span>
                  {selectedLocations.length > 0 && (
                    <button
                      onClick={() => setSelectedLocations([])}
                      className="text-[10px] text-indigo-400 hover:underline font-bold"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="relative">
                  <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
                  <input
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500"
                    placeholder="Search location..."
                    value={locationSearch}
                    onChange={(e) => setLocationSearch(e.target.value)}
                  />
                </div>

                <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                  {PRESET_LOCATIONS.filter((loc) =>
                    loc.toLowerCase().includes(locationSearch.toLowerCase())
                  ).map((loc) => (
                    <label
                      key={loc}
                      className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs text-slate-200 font-medium"
                    >
                      <input
                        type="checkbox"
                        checked={selectedLocations.includes(loc)}
                        onChange={() => toggleLocation(loc)}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>{loc}</span>
                    </label>
                  ))}
                </div>

                <div className="border-t border-slate-800 pt-2 space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Custom Location
                  </span>
                  <div className="flex gap-1.5">
                    <input
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-white placeholder-slate-500 outline-none"
                      placeholder="Add custom location..."
                      value={customLocationInput}
                      onChange={(e) => setCustomLocationInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addCustomLocation()}
                    />
                    <button
                      onClick={addCustomLocation}
                      className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold"
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Type Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowTypePopover(!showTypePopover);
                setShowLocationPopover(false);
                setShowExpPopover(false);
                setShowSkillPopover(false);
              }}
              className={`px-3.5 py-2 rounded-xl border text-xs font-semibold flex items-center gap-2 transition-all shadow-xs ${
                selectedTypes.length > 0
                  ? "bg-indigo-600 text-white border-indigo-500 shadow-indigo-600/20"
                  : "bg-slate-900 border-slate-800 text-slate-200 hover:border-slate-700"
              }`}
            >
              <BriefcaseBusiness size={14} className="text-indigo-400" />
              <span>
                {selectedTypes.length > 0 ? `Type (${selectedTypes.length})` : "Type"}
              </span>
              <ChevronDown size={14} />
            </button>

            {showTypePopover && (
              <div className="absolute left-0 top-12 w-56 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-3 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-white text-xs">Work Mode Type</span>
                  {selectedTypes.length > 0 && (
                    <button
                      onClick={() => setSelectedTypes([])}
                      className="text-[10px] text-indigo-400 hover:underline font-bold"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="space-y-1">
                  {PRESET_WORK_TYPES.map((type) => (
                    <label
                      key={type}
                      className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs text-slate-200 font-medium"
                    >
                      <input
                        type="checkbox"
                        checked={selectedTypes.includes(type)}
                        onChange={() => toggleType(type)}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>{type}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Experience Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowExpPopover(!showExpPopover);
                setShowLocationPopover(false);
                setShowTypePopover(false);
                setShowSkillPopover(false);
              }}
              className={`px-3.5 py-2 rounded-xl border text-xs font-semibold flex items-center gap-2 transition-all shadow-xs ${
                selectedExperience.length > 0
                  ? "bg-indigo-600 text-white border-indigo-500 shadow-indigo-600/20"
                  : "bg-slate-900 border-slate-800 text-slate-200 hover:border-slate-700"
              }`}
            >
              <span>
                {selectedExperience.length > 0
                  ? `Experience (${selectedExperience.length})`
                  : "Experience"}
              </span>
              <ChevronDown size={14} />
            </button>

            {showExpPopover && (
              <div className="absolute left-0 top-12 w-64 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-3 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-white text-xs">Experience Level</span>
                  {selectedExperience.length > 0 && (
                    <button
                      onClick={() => setSelectedExperience([])}
                      className="text-[10px] text-indigo-400 hover:underline font-bold"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {PRESET_EXPERIENCE_RANGES.map((exp) => (
                    <label
                      key={exp}
                      className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs text-slate-200 font-medium"
                    >
                      <input
                        type="checkbox"
                        checked={selectedExperience.includes(exp)}
                        onChange={() => toggleExperience(exp)}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>{exp}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Skills Filter Dropdown */}
          <div className="relative">
            <button
              onClick={() => {
                setShowSkillPopover(!showSkillPopover);
                setShowLocationPopover(false);
                setShowTypePopover(false);
                setShowExpPopover(false);
              }}
              className={`px-3.5 py-2 rounded-xl border text-xs font-semibold flex items-center gap-2 transition-all shadow-xs ${
                selectedSkills.length > 0
                  ? "bg-indigo-600 text-white border-indigo-500 shadow-indigo-600/20"
                  : "bg-slate-900 border-slate-800 text-slate-200 hover:border-slate-700"
              }`}
            >
              <Sparkles size={14} className="text-indigo-400" />
              <span>
                {selectedSkills.length > 0 ? `Skills (${selectedSkills.length})` : "Skills"}
              </span>
              <ChevronDown size={14} />
            </button>

            {showSkillPopover && (
              <div className="absolute left-0 top-12 w-72 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-3 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-white text-xs">Filter by Technical Skills</span>
                  {selectedSkills.length > 0 && (
                    <button
                      onClick={() => setSelectedSkills([])}
                      className="text-[10px] text-indigo-400 hover:underline font-bold"
                    >
                      Clear
                    </button>
                  )}
                </div>

                <div className="relative">
                  <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
                  <input
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500"
                    placeholder="Search skills..."
                    value={skillSearch}
                    onChange={(e) => setSkillSearch(e.target.value)}
                  />
                </div>

                <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                  {PRESET_SKILLS.filter((s) =>
                    s.toLowerCase().includes(skillSearch.toLowerCase())
                  ).map((s) => (
                    <label
                      key={s}
                      className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/80 cursor-pointer text-xs text-slate-200 font-medium"
                    >
                      <input
                        type="checkbox"
                        checked={selectedSkills.includes(s)}
                        onChange={() => toggleSkill(s)}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>{s}</span>
                    </label>
                  ))}
                </div>

                <div className="border-t border-slate-800 pt-2 space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    Custom Skill
                  </span>
                  <div className="flex gap-1.5">
                    <input
                      className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-white placeholder-slate-500 outline-none"
                      placeholder="Add custom skill..."
                      value={customSkillInput}
                      onChange={(e) => setCustomSkillInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addCustomSkill()}
                    />
                    <button
                      onClick={addCustomSkill}
                      className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold"
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Clear Filters Button */}
          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="px-3.5 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 text-xs font-bold flex items-center gap-1.5 transition-all"
            >
              <FilterX size={14} /> Clear Filters
            </button>
          )}
        </div>

        {/* Selected Filter Badges */}
        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            {selectedLocations.map((loc) => (
              <span
                key={loc}
                className="px-2.5 py-1 rounded-md bg-indigo-950 border border-indigo-800 text-indigo-300 text-[11px] font-semibold flex items-center gap-1"
              >
                📍 {loc}
                <button onClick={() => toggleLocation(loc)} className="hover:text-white">
                  <X size={12} />
                </button>
              </span>
            ))}
            {selectedTypes.map((type) => (
              <span
                key={type}
                className="px-2.5 py-1 rounded-md bg-indigo-950 border border-indigo-800 text-indigo-300 text-[11px] font-semibold flex items-center gap-1"
              >
                💼 {type}
                <button onClick={() => toggleType(type)} className="hover:text-white">
                  <X size={12} />
                </button>
              </span>
            ))}
            {selectedExperience.map((exp) => (
              <span
                key={exp}
                className="px-2.5 py-1 rounded-md bg-indigo-950 border border-indigo-800 text-indigo-300 text-[11px] font-semibold flex items-center gap-1"
              >
                ⏳ {exp.split(" ")[0]}
                <button onClick={() => toggleExperience(exp)} className="hover:text-white">
                  <X size={12} />
                </button>
              </span>
            ))}
            {selectedSkills.map((s) => (
              <span
                key={s}
                className="px-2.5 py-1 rounded-md bg-emerald-950 border border-emerald-800 text-emerald-300 text-[11px] font-semibold flex items-center gap-1"
              >
                ⚡ {s}
                <button onClick={() => toggleSkill(s)} className="hover:text-white">
                  <X size={12} />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Main Content Layout */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
        <main className="space-y-4">
          <div className="flex items-center justify-between pb-1">
            <div>
              <h2 className="font-bold text-white text-base">
                {totalFiltered} Requisitions Found
              </h2>
              <p className="mt-0.5 text-xs text-slate-400">
                <strong className="text-emerald-400">Verified Active &amp; Approved</strong> jobs accepting candidate applications
              </p>
            </div>
            <button className="px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 text-xs font-semibold flex items-center gap-1">
              Best match <ChevronDown size={13} />
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500 font-semibold animate-pulse">
              Loading public job listings...
            </div>
          ) : paginatedJobs.length === 0 ? (
            <div className="p-8 rounded-xl border border-slate-800 bg-slate-900 text-center text-xs text-slate-400 space-y-2">
              <p className="font-bold text-white">No job requisitions match your active filters.</p>
              <p className="text-slate-500">Try removing some filter criteria or clearing all filters.</p>
              <button
                onClick={clearAllFilters}
                className="mt-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold inline-flex items-center gap-1"
              >
                <FilterX size={14} /> Clear All Filters
              </button>
            </div>
          ) : (
            <>
              {/* Jobs List (15 items per page) */}
              <div className="space-y-4">
                {paginatedJobs.map((job) => (
                  <article
                    key={job.id}
                    className="p-5 sm:p-6 rounded-xl border border-slate-800 bg-slate-900 text-white shadow-xs hover:border-slate-700 transition-all"
                  >
                    <div className="flex gap-4">
                      <div className="w-12 h-12 rounded-xl bg-indigo-950/80 border border-indigo-900 text-indigo-300 font-bold grid place-items-center text-lg shrink-0">
                        {job.company?.[0] || "A"}
                      </div>

                      <div className="min-w-0 flex-1 space-y-3">
                        <div className="flex flex-wrap justify-between gap-3">
                          <div>
                            <h3 className="font-bold text-white text-base">
                              {job.title}
                            </h3>
                            <p className="mt-0.5 text-xs text-slate-300 font-medium">
                              {job.company}
                            </p>
                            <p className="mt-1 flex items-center gap-2 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <MapPin size={13} /> {job.location}
                              </span>
                              <span>•</span>
                              <span className="flex items-center gap-1">
                                <BriefcaseBusiness size={13} /> {job.work_mode}
                              </span>
                            </p>
                          </div>
                        </div>

                        <div className="mt-4 flex items-center justify-between border-t border-slate-800 pt-3">
                          <span className="text-xs text-slate-400 font-medium">
                            {job.salary ? `${job.salary} • ` : ""}Posted {job.posted}
                          </span>
                          <div className="flex gap-2">
                            <Link
                              href={`/jobs/${job.id}`}
                              className="px-4 py-2 rounded-lg border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs font-semibold transition-all"
                            >
                              View
                            </Link>
                            <Link
                              href={`/career?jobId=${job.id}`}
                              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
                            >
                              <Sparkles size={14} /> Apply with AI
                            </Link>
                          </div>
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>

              {/* 10 Jobs Per Page Pagination Controls */}
              {totalPages > 1 && (
                <div className="p-4 rounded-xl border border-slate-800 bg-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4 mt-6">
                  <div className="text-xs text-slate-400 font-medium">
                    Showing <strong className="text-white">{startIndex + 1}</strong> –{" "}
                    <strong className="text-white">{endIndex}</strong> of{" "}
                    <strong className="text-white">{totalFiltered}</strong> positions
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Previous Button */}
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center gap-1 transition-all ${
                        currentPage === 1
                          ? "border-slate-800 text-slate-600 cursor-not-allowed"
                          : "border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
                      }`}
                    >
                      <ChevronLeft size={15} /> Previous
                    </button>

                    {/* Page Numbers */}
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                          currentPage === pageNum
                            ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                            : "bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                        }`}
                      >
                        {pageNum}
                      </button>
                    ))}

                    {/* Next Button */}
                    <button
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className={`px-3 py-1.5 rounded-lg border text-xs font-bold flex items-center gap-1 transition-all ${
                        currentPage === totalPages
                          ? "border-slate-800 text-slate-600 cursor-not-allowed"
                          : "border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700"
                      }`}
                    >
                      Next <ChevronRight size={15} />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </main>

        <aside className="space-y-4">
          <div className="p-5 rounded-xl border border-slate-800 bg-slate-900 text-white shadow-xs">
            <h2 className="font-bold text-white text-sm">Your match profile</h2>
            <p className="mt-2 text-xs leading-relaxed text-slate-300">
              Your strongest roles match Python, Machine Learning, and scalable backend architecture.
            </p>
            <div className="mt-4 space-y-3">
              {[
                ["Skills", 92],
                ["Experience", 86],
                ["Projects", 88],
              ].map(([label, value]) => (
                <div key={String(label)}>
                  <div className="mb-1 flex justify-between text-xs font-semibold text-slate-300">
                    <span>{label}</span>
                    <strong className="text-indigo-400">{value}%</strong>
                  </div>
                  <div className="progress-track bg-slate-800">
                    <span style={{ width: `${value}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <Link
              href="/candidate/profile"
              className="mt-5 block text-xs font-bold text-indigo-400 hover:underline"
            >
              Improve your match profile &rarr;
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
