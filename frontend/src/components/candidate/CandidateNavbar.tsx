"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";
import { apiFetch } from "@/lib/api";
import {
  Bell,
  Briefcase,
  BriefcaseBusiness,
  Building2,
  Calendar,
  Check,
  ChevronDown,
  CircleUserRound,
  LayoutDashboard,
  LogOut,
  MessageCircle,
  Moon,
  Search,
  Settings,
  Sparkles,
  Sun,
  User,
  UserRound,
  UsersRound,
} from "lucide-react";

export function CandidateNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<"light" | "dark">("light");

  // Profile data state
  const [profile, setProfile] = useState<any>(null);

  // Dropdown states
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const [showNotificationsDropdown, setShowNotificationsDropdown] = useState(false);
  const [showMessagesDropdown, setShowMessagesDropdown] = useState(false);
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState("");

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.classList.add("dark");

    async function fetchCandidateProfile() {
      try {
        const res = await apiFetch("/api/v1/candidate/profile");
        if (res.ok) {
          const data = await res.json();
          setProfile(data);
        }
      } catch (err) {
        console.error("Error fetching profile in navbar:", err);
      }
    }
    fetchCandidateProfile();
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowSearchDropdown(false);
        setShowNotificationsDropdown(false);
        setShowMessagesDropdown(false);
        setShowProfileDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("candidate_theme_pref", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
  };

  const navItems = [
    { label: "Home", href: "/candidate/dashboard", icon: LayoutDashboard },
    { label: "Jobs", href: "/jobs", icon: BriefcaseBusiness },
    { label: "Applications", href: "/candidate/applications", icon: CircleUserRound },
    { label: "Network", href: "/network", icon: UsersRound },
    { label: "AI Career", href: "/career", icon: Sparkles },
    { label: "Messages", href: "/messages", icon: MessageCircle },
  ];

  // Matched jobs (> 50% match) for Bell Notifications
  const matchedJobNotifications = [
    {
      id: "generative-ai-engineer",
      title: "Generative AI Engineer",
      company: "Aster Labs",
      match: 94,
      posted: "2 hours ago",
    },
    {
      id: "backend-engineer-python",
      title: "Backend Engineer – Python",
      company: "UG/PG - Computer Science",
      match: 91,
      posted: "5 hours ago",
    },
    {
      id: "machine-learning-engineer",
      title: "Machine Learning Engineer",
      company: "Artificial Intelligence Requisition",
      match: 87,
      posted: "1 day ago",
    },
  ];

  // Recruiter Messages & Interviews for Message Icon Dropdown
  const messageNotifications = [
    {
      id: "m1",
      sender: "Santhosh Kumar",
      role: "Lead Recruiter @ Enterprise Hiring AI",
      type: "INTERVIEW",
      subject: "Stage 3 Technical Discussion Scheduled",
      time: "10:45 AM",
    },
    {
      id: "m2",
      sender: "Dr. Ananya Sharma",
      role: "AI Acquisition Lead @ Aster Labs",
      type: "MESSAGE",
      subject: "Updated GitHub & Code Portfolio Link Request",
      time: "Yesterday",
    },
  ];

  // Search Data Source
  const searchResults = [
    { type: "JOB", title: "Generative AI Engineer", subtitle: "Aster Labs • 94% Match", href: "/jobs/generative-ai-engineer" },
    { type: "JOB", title: "Backend Engineer – Python", subtitle: "UG/PG - Computer Science • 91% Match", href: "/jobs/backend-engineer-python" },
    { type: "JOB", title: "Machine Learning Engineer", subtitle: "Artificial Intelligence • 87% Match", href: "/jobs/machine-learning-engineer" },
    { type: "COMPANY", title: "Aster Labs", subtitle: "AI Research & Scale Enterprise", href: "/jobs" },
    { type: "PEOPLE", title: "Santhosh Kumar", subtitle: "Lead Recruiter @ Enterprise Hiring AI", href: "/network" },
    { type: "PEOPLE", title: "Dr. Ananya Sharma", subtitle: "AI Acquisition Lead @ Aster Labs", href: "/network" },
    { type: "SKILL", title: "Python 3.13 & FastAPI", subtitle: "Matching 12 open positions", href: "/jobs" },
    { type: "SKILL", title: "Generative AI & RAG", subtitle: "Matching 8 open positions", href: "/jobs" },
  ].filter(
    (item) =>
      !searchQuery.trim() ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.subtitle.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <>
      <header className="hiring-header">
        <div className="hiring-header-inner" ref={dropdownRef}>
          {/* Brand */}
          <div className="flex items-center space-x-6">
            <Link href="/candidate/dashboard" className="brand">
              <span className="brand-mark">
                <Sparkles size={17} />
              </span>
              <span>
                Hiring<span>AI</span>
              </span>
            </Link>
          </div>

          {/* Requirement 2: Global Search Bar with Live Popover Dropdown */}
          <div className="relative max-w-[520px] w-full hidden md:block">
            <label className="global-search">
              <Search size={17} className="text-slate-400" />
              <input
                aria-label="Global search"
                placeholder="Search jobs, companies, people, skills..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowSearchDropdown(true);
                }}
                onFocus={() => setShowSearchDropdown(true)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && searchQuery.trim()) {
                    setShowSearchDropdown(false);
                    router.push(`/jobs?q=${encodeURIComponent(searchQuery)}`);
                  }
                }}
              />
            </label>

            {/* Search Results Dropdown */}
            {showSearchDropdown && (
              <div className="absolute top-12 left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl overflow-hidden z-50 p-2 space-y-1">
                <div className="p-2 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                  <span>Live Search Results ({searchResults.length})</span>
                  <span className="text-indigo-600 dark:text-indigo-400 font-mono">Press Enter to view all</span>
                </div>
                <div className="max-h-80 overflow-y-auto space-y-1">
                  {searchResults.length === 0 ? (
                    <div className="p-4 text-center text-xs text-slate-500">
                      No matches found for &quot;{searchQuery}&quot;
                    </div>
                  ) : (
                    searchResults.map((item, idx) => (
                      <Link
                        key={idx}
                        href={item.href}
                        onClick={() => setShowSearchDropdown(false)}
                        className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-all text-xs"
                      >
                        <span className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-bold shrink-0">
                          {item.type === "JOB" && <Briefcase size={14} />}
                          {item.type === "COMPANY" && <Building2 size={14} />}
                          {item.type === "PEOPLE" && <User size={14} />}
                          {item.type === "SKILL" && <Sparkles size={14} />}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="font-bold text-slate-900 dark:text-white truncate">
                            {item.title}
                          </p>
                          <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                            {item.subtitle}
                          </p>
                        </div>
                      </Link>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Header Actions */}
          <div className="header-actions relative">
            {/* Requirement 3: Bell Icon Notifications Dropdown (> 50% Match Jobs) */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowNotificationsDropdown(!showNotificationsDropdown);
                  setShowMessagesDropdown(false);
                  setShowProfileDropdown(false);
                }}
                aria-label="Job Notifications"
                title="Job Notifications (> 50% Match)"
                className="icon-button relative"
              >
                <Bell size={19} />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 text-white rounded-full text-[9px] font-extrabold flex items-center justify-center shadow-xs">
                  {matchedJobNotifications.length}
                </span>
              </button>

              {showNotificationsDropdown && (
                <div className="absolute right-0 top-11 w-80 sm:w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-3 space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2 px-1">
                    <h4 className="font-bold text-slate-900 dark:text-white text-xs">
                      Matched Job Notifications (&gt; 50% Match)
                    </h4>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold">
                      3 New
                    </span>
                  </div>

                  <div className="space-y-1.5 max-h-80 overflow-y-auto">
                    {matchedJobNotifications.map((job) => (
                      <Link
                        key={job.id}
                        href={`/jobs/${job.id}`}
                        onClick={() => setShowNotificationsDropdown(false)}
                        className="block p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-all border border-slate-100 dark:border-slate-800/60 space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900 dark:text-white text-xs">
                            {job.title}
                          </span>
                          <span className="px-2 py-0.5 rounded-md bg-emerald-500 text-white text-[10px] font-extrabold">
                            {job.match}% MATCH
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">
                          {job.company} • Posted {job.posted}
                        </p>
                      </Link>
                    ))}
                  </div>

                  <Link
                    href="/jobs"
                    onClick={() => setShowNotificationsDropdown(false)}
                    className="block text-center text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline pt-1"
                  >
                    View All Matched Jobs &rarr;
                  </Link>
                </div>
              )}
            </div>

            {/* Requirement 4: Message Icon Dropdown (Interviews & Recruiter Messages) */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowMessagesDropdown(!showMessagesDropdown);
                  setShowNotificationsDropdown(false);
                  setShowProfileDropdown(false);
                }}
                aria-label="Recruiter Messages & Interviews"
                title="Recruiter Messages & Interview Schedule"
                className="icon-button relative"
              >
                <MessageCircle size={19} />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-indigo-600 text-white rounded-full text-[9px] font-extrabold flex items-center justify-center shadow-xs">
                  {messageNotifications.length}
                </span>
              </button>

              {showMessagesDropdown && (
                <div className="absolute right-0 top-11 w-80 sm:w-96 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-3 space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2 px-1">
                    <h4 className="font-bold text-slate-900 dark:text-white text-xs">
                      Recruiter &amp; Interview Alerts
                    </h4>
                    <span className="px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 text-[10px] font-bold">
                      2 Unread
                    </span>
                  </div>

                  <div className="space-y-1.5 max-h-80 overflow-y-auto">
                    {messageNotifications.map((msg) => (
                      <Link
                        key={msg.id}
                        href="/messages"
                        onClick={() => setShowMessagesDropdown(false)}
                        className="block p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-all border border-slate-100 dark:border-slate-800/60 space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900 dark:text-white text-xs flex items-center gap-1.5">
                            {msg.type === "INTERVIEW" ? (
                              <Calendar size={13} className="text-indigo-600 dark:text-indigo-400" />
                            ) : (
                              <MessageCircle size={13} className="text-sky-500" />
                            )}
                            {msg.sender}
                          </span>
                          <span className="text-[10px] text-slate-400">{msg.time}</span>
                        </div>
                        <p className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">
                          {msg.subject}
                        </p>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                          {msg.role}
                        </p>
                      </Link>
                    ))}
                  </div>

                  <Link
                    href="/messages"
                    onClick={() => setShowMessagesDropdown(false)}
                    className="block text-center text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline pt-1"
                  >
                    Go to Messages Page &rarr;
                  </Link>
                </div>
              )}
            </div>

            {/* Requirement 5: Candidate Profile Avatar with Dropdown Menu */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowProfileDropdown(!showProfileDropdown);
                  setShowNotificationsDropdown(false);
                  setShowMessagesDropdown(false);
                }}
                className="avatar-button focus:outline-none"
                title="Profile Account Menu"
              >
                {profile?.photo_url ? (
                  <img
                    src={profile.photo_url}
                    alt={user?.full_name || "Profile"}
                    className="w-8 h-8 rounded-full object-cover border border-indigo-300 dark:border-indigo-700 shadow-xs"
                  />
                ) : (
                  <span>{user?.full_name?.charAt(0).toUpperCase() || "G"}</span>
                )}
                <ChevronDown size={15} className="text-slate-600 dark:text-slate-300" />
              </button>

              {/* Avatar Dropdown Menu */}
              {showProfileDropdown && (
                <div className="absolute right-0 top-11 w-56 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden z-50 p-2 space-y-1">
                  <div className="p-2.5 border-b border-slate-100 dark:border-slate-800">
                    <p className="font-bold text-slate-900 dark:text-white text-xs truncate">
                      {user?.full_name || "Candidate Account"}
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                      {user?.email}
                    </p>
                  </div>

                  <div className="space-y-0.5 pt-1">
                    <Link
                      href="/candidate/profile"
                      onClick={() => setShowProfileDropdown(false)}
                      className="flex items-center gap-2.5 p-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
                    >
                      <UserRound size={15} className="text-indigo-600 dark:text-indigo-400" />
                      <span>Edit Profile</span>
                    </Link>

                    <Link
                      href="/jobs"
                      onClick={() => setShowProfileDropdown(false)}
                      className="flex items-center gap-2.5 p-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
                    >
                      <BriefcaseBusiness size={15} className="text-emerald-600 dark:text-emerald-400" />
                      <span>Apply Job</span>
                    </Link>

                    <Link
                      href="/messages"
                      onClick={() => setShowProfileDropdown(false)}
                      className="flex items-center gap-2.5 p-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
                    >
                      <MessageCircle size={15} className="text-sky-500" />
                      <span>Messages</span>
                    </Link>

                    <Link
                      href="/settings"
                      onClick={() => setShowProfileDropdown(false)}
                      className="flex items-center gap-2.5 p-2 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
                    >
                      <Settings size={15} className="text-slate-500" />
                      <span>Settings</span>
                    </Link>
                  </div>

                  <div className="border-t border-slate-100 dark:border-slate-800 pt-1">
                    <button
                      onClick={() => {
                        setShowProfileDropdown(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-2.5 p-2 rounded-lg text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-all"
                    >
                      <LogOut size={15} />
                      <span>Log Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="hiring-sidebar">
        <nav>
          {navItems.map(({ label, href, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={pathname === href ? "nav-link active" : "nav-link"}
            >
              <Icon size={18} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <Link href="/candidate/profile" className="nav-link">
            <UserRound size={18} />
            <span>Profile</span>
          </Link>
          <Link href="/settings" className="nav-link">
            <Settings size={18} />
            <span>Settings</span>
          </Link>
          <div className="ai-side-card">
            <Sparkles size={16} />
            <strong>Your profile is 82% ready</strong>
            <Link href="/candidate/profile">Improve profile</Link>
          </div>
        </div>
      </aside>

      {/* Mobile Navigation */}
      <nav className="mobile-nav">
        {[
          navItems[0],
          navItems[1],
          navItems[4],
          navItems[5],
          { label: "Profile", href: "/candidate/profile", icon: UserRound },
        ].map(({ label, href, icon: Icon }) => (
          <Link key={href} href={href} className={pathname === href ? "active" : ""}>
            <Icon size={20} />
            <span>{label}</span>
          </Link>
        ))}
      </nav>
    </>
  );
}
