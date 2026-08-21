"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  Bell,
  Briefcase,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ChevronDown,
  Command,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  PlusCircle,
  Search,
  Sparkles,
  User,
  Users,
  UsersRound,
  X,
} from "lucide-react";
import { useAuth } from "@/components/auth/AuthContext";

const links = [
  { label: "Overview", href: "/recruiter/dashboard", icon: LayoutDashboard },
  { label: "Jobs", href: "/recruiter/jobs", icon: BriefcaseBusiness },
  { label: "Candidates", href: "/recruiter/jobs", icon: UsersRound },
  { label: "AI matching", href: "/recruiter/jobs", icon: Sparkles },
  { label: "Interviews", href: "/recruiter/jobs", icon: CalendarDays },
  { label: "Messages", href: "/recruiter/jobs", icon: MessageSquare },
  { label: "Analytics", href: "/recruiter/reports", icon: BarChart3 },
  { label: "Company", href: "/recruiter/organization/members", icon: Building2 },
];

interface NotificationItem {
  id: string;
  type: "job" | "candidate" | "ai";
  title: string;
  description: string;
  timestamp: string;
  read: boolean;
  link: string;
}

const initialNotifications: NotificationItem[] = [
  {
    id: "1",
    type: "ai",
    title: "AI Match Fit Signal Ready",
    description: "11 candidates meet or exceed the interview threshold for Senior ML Engineer.",
    timestamp: "10m ago",
    read: false,
    link: "/recruiter/jobs/1/ranking",
  },
  {
    id: "2",
    type: "candidate",
    title: "New Candidate Application",
    description: "Gnanendhra Joy submitted an application with verified RAG & FastAPI evidence.",
    timestamp: "32m ago",
    read: false,
    link: "/recruiter/jobs/1/applications",
  },
  {
    id: "3",
    type: "job",
    title: "Requisition Published",
    description: "Requisition 'Product Designer' is now active across all candidate channels.",
    timestamp: "2h ago",
    read: true,
    link: "/recruiter/jobs",
  },
  {
    id: "4",
    type: "candidate",
    title: "Interview Slot Accepted",
    description: "Rohan Iyer accepted the scheduled technical interview invitation.",
    timestamp: "4h ago",
    read: true,
    link: "/recruiter/jobs/1/interviews",
  },
];

interface SearchResultItem {
  id: string;
  type: "candidate" | "job" | "company";
  title: string;
  subtitle: string;
  tag: string;
  link: string;
}

const searchDatabase: SearchResultItem[] = [
  {
    id: "c1",
    type: "candidate",
    title: "Gnanendhra Joy",
    subtitle: "AI/ML Engineer • Python, RAG, FastAPI",
    tag: "96% Match",
    link: "/recruiter/jobs/1/applications",
  },
  {
    id: "c2",
    type: "candidate",
    title: "Aisha Rahman",
    subtitle: "Applied AI Engineer • LLMs, PyTorch, AWS",
    tag: "93% Match",
    link: "/recruiter/jobs/1/applications",
  },
  {
    id: "c3",
    type: "candidate",
    title: "Rohan Iyer",
    subtitle: "Machine Learning Engineer • Python, SQL, Vector DBs",
    tag: "91% Match",
    link: "/recruiter/jobs/1/applications",
  },
  {
    id: "c4",
    type: "candidate",
    title: "Meera Shah",
    subtitle: "Data Scientist • Python, NLP, MLflow",
    tag: "88% Match",
    link: "/recruiter/jobs/1/applications",
  },
  {
    id: "j1",
    type: "job",
    title: "Senior ML Engineer",
    subtitle: "Engineering • 1,284 Applications",
    tag: "Active Job",
    link: "/recruiter/jobs/1",
  },
  {
    id: "j2",
    type: "job",
    title: "Product Designer",
    subtitle: "Design • 4 candidates awaiting review",
    tag: "Needs Review",
    link: "/recruiter/jobs",
  },
  {
    id: "j3",
    type: "job",
    title: "Backend Architect",
    subtitle: "Infrastructure • Requisition open",
    tag: "Active Job",
    link: "/recruiter/jobs",
  },
  {
    id: "o1",
    type: "company",
    title: "Rao Enterprise",
    subtitle: "Hiring Organization & Workspace Team",
    tag: "Company",
    link: "/recruiter/organization/members",
  },
];

export function RecruiterConsoleNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, memberships, logout } = useAuth();

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchCategory, setSearchCategory] = useState<"all" | "candidate" | "job" | "company">("all");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Notification state
  const [notifications, setNotifications] = useState<NotificationItem[]>(initialNotifications);
  const [notifCategory, setNotifCategory] = useState<"all" | "job" | "candidate" | "ai">("all");
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  // Profile dropdown state
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close popovers on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setIsNotifOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Compute initials fallback
  const userFullName = user?.full_name?.trim() || "Kavya Sharma";
  const userEmail = user?.email || "recruiter@hiringai.com";
  const userPhoto = (user as any)?.photo_url || null;
  const orgName = memberships?.[0]?.organization_name || "Rao Enterprise";

  const getInitials = (name: string) => {
    const parts = name.split(" ").filter(Boolean);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    if (parts.length === 1 && parts[0].length > 0) {
      return parts[0].substring(0, 2).toUpperCase();
    }
    return "KS";
  };

  const initials = getInitials(userFullName);

  // Filtered search results
  const filteredSearch = searchDatabase.filter((item) => {
    const matchesCategory = searchCategory === "all" || item.type === searchCategory;
    const matchesQuery =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.subtitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tag.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  // Filtered notifications
  const filteredNotifs = notifications.filter(
    (n) => notifCategory === "all" || n.type === notifCategory
  );

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  return (
    <>
      <header className="command-header">
        {/* Brand */}
        <Link className="command-brand" href="/recruiter/dashboard">
          <span>
            <Command size={17} />
          </span>
          HiringAI <em>Talent OS</em>
        </Link>

        {/* Global Search with Category Filtering */}
        <div ref={searchRef} className="relative flex-1 max-w-[420px]">
          <label className="command-search w-full cursor-text">
            <Search size={16} />
            <input
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setIsSearchOpen(true);
              }}
              onFocus={() => setIsSearchOpen(true)}
              placeholder="Search candidates, jobs, or companies..."
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setIsSearchOpen(false);
                }}
                className="text-slate-400 hover:text-slate-200"
              >
                <X size={14} />
              </button>
            )}
          </label>

          {/* Search Dropdown */}
          {isSearchOpen && (
            <div className="absolute top-[48px] left-0 right-0 z-50 bg-[#111a2c] border border-[#233047] rounded-lg shadow-2xl overflow-hidden text-xs">
              {/* Filter Pills */}
              <div className="flex items-center gap-1.5 p-2 bg-[#0b1425] border-b border-[#233047]">
                {(["all", "candidate", "job", "company"] as const).map((cat) => (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSearchCategory(cat)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-semibold capitalize transition ${
                      searchCategory === cat
                        ? "bg-[#2563eb] text-white"
                        : "bg-[#18253a] text-slate-400 hover:text-slate-200 hover:bg-[#1e3250]"
                    }`}
                  >
                    {cat === "company" ? "Roles & Orgs" : cat}
                  </button>
                ))}
              </div>

              {/* Search Results */}
              <div className="max-h-[320px] overflow-y-auto divide-y divide-[#1d2a40]">
                {filteredSearch.length > 0 ? (
                  filteredSearch.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => {
                        setIsSearchOpen(false);
                        router.push(item.link);
                      }}
                      className="flex items-center justify-between p-3 hover:bg-[#18253a] cursor-pointer transition"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-[#0b1425] text-sky-400 border border-[#1e3250]">
                          {item.type === "candidate" ? (
                            <Users size={15} />
                          ) : item.type === "job" ? (
                            <Briefcase size={15} />
                          ) : (
                            <Building2 size={15} />
                          )}
                        </div>
                        <div>
                          <div className="font-bold text-slate-100">{item.title}</div>
                          <div className="text-[11px] text-slate-400">{item.subtitle}</div>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-[#162a45] text-sky-300 border border-[#23456e]">
                        {item.tag}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-slate-400">
                    No results found for &quot;<span className="text-slate-200">{searchQuery}</span>&quot;
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Action Controls & Profile Avatar */}
        <div className="command-actions relative flex items-center gap-3">
          {/* Notifications Bell */}
          <div ref={notifRef} className="relative">
            <button
              type="button"
              onClick={() => {
                setIsNotifOpen(!isNotifOpen);
                setIsProfileOpen(false);
              }}
              className="relative p-2 rounded-lg bg-[#111a2c] hover:bg-[#18253a] text-slate-300 transition"
              title="Notifications"
            >
              <Bell size={18} />
              {unreadCount > 0 && <i className="absolute top-1 right-1 w-2 h-2 rounded-full bg-sky-400" />}
            </button>

            {/* Notification Drawer Popover */}
            {isNotifOpen && (
              <div className="absolute right-0 top-[48px] z-50 w-[360px] bg-[#111a2c] border border-[#233047] rounded-lg shadow-2xl overflow-hidden text-xs">
                {/* Header */}
                <div className="flex items-center justify-between p-3 bg-[#0b1425] border-b border-[#233047]">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-100 text-sm">Notifications</span>
                    {unreadCount > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                        {unreadCount} new
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      type="button"
                      onClick={markAllRead}
                      className="text-[11px] font-semibold text-sky-400 hover:text-sky-300 transition"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>

                {/* Filter Tabs */}
                <div className="flex items-center gap-1 p-2 bg-[#0d1728] border-b border-[#1d2a40]">
                  {(["all", "job", "candidate", "ai"] as const).map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => setNotifCategory(cat)}
                      className={`px-2 py-1 rounded text-[10px] font-semibold capitalize transition ${
                        notifCategory === cat
                          ? "bg-[#2563eb] text-white"
                          : "bg-[#18253a] text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      {cat === "ai" ? "AI Signals" : cat}
                    </button>
                  ))}
                </div>

                {/* Notifications List */}
                <div className="max-h-[320px] overflow-y-auto divide-y divide-[#1d2a40]">
                  {filteredNotifs.length > 0 ? (
                    filteredNotifs.map((n) => (
                      <div
                        key={n.id}
                        onClick={() => {
                          markAsRead(n.id);
                          setIsNotifOpen(false);
                          router.push(n.link);
                        }}
                        className={`p-3 hover:bg-[#18253a] cursor-pointer transition flex items-start gap-3 ${
                          !n.read ? "bg-[#132238]/60" : ""
                        }`}
                      >
                        <div className="p-1.5 rounded bg-[#0b1425] text-sky-400 border border-[#1e3250] mt-0.5">
                          {n.type === "ai" ? (
                            <Sparkles size={14} />
                          ) : n.type === "candidate" ? (
                            <Users size={14} />
                          ) : (
                            <Briefcase size={14} />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className={`font-semibold ${!n.read ? "text-slate-100" : "text-slate-300"}`}>
                              {n.title}
                            </span>
                            <span className="text-[10px] text-slate-500">{n.timestamp}</span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-1 leading-snug">{n.description}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-6 text-center text-slate-500">No notifications in this view.</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Profile Avatar & Dropdown */}
          <div ref={profileRef} className="relative">
            <button
              type="button"
              onClick={() => {
                setIsProfileOpen(!isProfileOpen);
                setIsNotifOpen(false);
              }}
              className="command-avatar hover:bg-[#254877] transition cursor-pointer"
            >
              {userPhoto ? (
                <img src={userPhoto} alt={userFullName} className="w-5 h-5 rounded-full object-cover" />
              ) : (
                <span>{initials}</span>
              )}
              <ChevronDown size={14} />
            </button>

            {/* Profile Popover Menu */}
            {isProfileOpen && (
              <div className="absolute right-0 top-[48px] z-50 w-[240px] bg-[#111a2c] border border-[#233047] rounded-lg shadow-2xl overflow-hidden text-xs">
                {/* User Info Header */}
                <div className="p-3 bg-[#0b1425] border-b border-[#233047]">
                  <div className="flex items-center gap-2.5">
                    {userPhoto ? (
                      <img src={userPhoto} alt={userFullName} className="w-8 h-8 rounded-full object-cover" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-[#1e3a5f] text-sky-200 font-extrabold flex items-center justify-center text-xs">
                        {initials}
                      </div>
                    )}
                    <div className="overflow-hidden">
                      <div className="font-bold text-slate-100 truncate">{userFullName}</div>
                      <div className="text-[11px] text-slate-400 truncate">{userEmail}</div>
                    </div>
                  </div>
                  <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-[#1d2a40]">
                    <span className="text-[10px] font-bold text-sky-400 uppercase tracking-wider">Recruiter</span>
                    <span className="text-[10px] text-slate-400 truncate max-w-[120px]">{orgName}</span>
                  </div>
                </div>

                {/* Menu Items */}
                <div className="p-1.5 divide-y divide-[#1d2a40]">
                  <div className="py-1">
                    <button
                      type="button"
                      onClick={() => {
                        setIsProfileOpen(false);
                        router.push("/recruiter/organization/members");
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-300 hover:text-white hover:bg-[#18253a] rounded-md transition"
                    >
                      <User size={14} className="text-sky-400" />
                      <span>Edit Profile</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setIsProfileOpen(false);
                        router.push("/recruiter/jobs/new");
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-300 hover:text-white hover:bg-[#18253a] rounded-md transition"
                    >
                      <PlusCircle size={14} className="text-emerald-400" />
                      <span>Add New Job</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setIsProfileOpen(false);
                        setIsNotifOpen(true);
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-300 hover:text-white hover:bg-[#18253a] rounded-md transition"
                    >
                      <Bell size={14} className="text-amber-400" />
                      <span>Notifications</span>
                      {unreadCount > 0 && (
                        <span className="ml-auto px-1.5 py-0.2 text-[9px] font-bold rounded-full bg-sky-500 text-white">
                          {unreadCount}
                        </span>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setIsProfileOpen(false);
                        router.push("/recruiter/organization/members");
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-300 hover:text-white hover:bg-[#18253a] rounded-md transition"
                    >
                      <Building2 size={14} className="text-purple-400" />
                      <span>Company & Team</span>
                    </button>
                  </div>

                  {/* Log Out */}
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setIsProfileOpen(false);
                        logout("/login");
                      }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-rose-400 hover:text-rose-300 hover:bg-[#25141e] rounded-md transition font-semibold"
                    >
                      <LogOut size={14} />
                      <span>Log Out</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="command-sidebar">
        <p>Workspace</p>
        {links.map(({ label, href, icon: Icon }) => (
          <Link key={label} href={href} className={pathname === href ? "active" : ""}>
            <Icon size={17} />
            {label}
          </Link>
        ))}
        <div className="command-upgrade">
          <Sparkles size={15} />
          <strong>AI hiring signal</strong>
          <span>84 candidates ready to review</span>
          <Link href="/recruiter/jobs">Open shortlist →</Link>
        </div>
      </aside>
    </>
  );
}
