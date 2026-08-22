"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";
import {
  Bell,
  BriefcaseBusiness,
  ChevronDown,
  CircleUserRound,
  LayoutDashboard,
  MessageCircle,
  Moon,
  Search,
  Settings,
  Sparkles,
  Sun,
  UserRound,
  UsersRound,
} from "lucide-react";

export function CandidateNavbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const savedTheme = localStorage.getItem("candidate_theme_pref");
    if (savedTheme === "dark" || savedTheme === "light") {
      setTheme(savedTheme);
      document.documentElement.classList.toggle("dark", savedTheme === "dark");
    } else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
      document.documentElement.classList.toggle("dark", prefersDark);
    }
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

  return (
    <>
      <header className="hiring-header">
        <div className="hiring-header-inner">
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

            {/* Navigation Links */}
            <nav className="hidden">
              {navItems.map((item) => (
                <Link key={item.href} href={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Search bar */}
          <label className="global-search">
            <Search size={17} />
            <input aria-label="Global search" placeholder="Search jobs, companies, people..." />
          </label>

          {/* Right Header Actions */}
          <div className="header-actions">
            {/* Bell Icon Notifications */}
            <button aria-label="Notifications" className="icon-button" title="Notifications">
              <Bell size={19} />
              <i />
            </button>

            {/* Dark & Light UI Theme Toggle Button beside Bell Icon */}
            <button
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
              title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="icon-button transition-transform hover:scale-105"
            >
              {theme === "dark" ? (
                <Sun size={19} className="text-amber-400 hover:text-amber-300 transition-colors" />
              ) : (
                <Moon size={19} className="text-slate-600 hover:text-indigo-600 transition-colors" />
              )}
            </button>

            {/* Messages */}
            <Link aria-label="Messages" title="Messages" href="/messages" className="icon-button">
              <MessageCircle size={19} />
            </Link>

            {/* Avatar & Profile dropdown */}
            <button onClick={() => logout()} className="avatar-button" title="Account Menu / Sign Out">
              <span>{user?.full_name?.charAt(0).toUpperCase() || "G"}</span>
              <ChevronDown size={15} />
            </button>
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
