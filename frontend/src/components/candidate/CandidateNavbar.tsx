"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";

export function CandidateNavbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { label: "Dashboard", href: "/candidate/dashboard" },
    { label: "Applications", href: "/candidate/applications" },
    { label: "Assessments", href: "/candidate/assessments" },
    { label: "Interviews", href: "/candidate/interviews" },
    { label: "Profile", href: "/candidate/profile" },
    { label: "Browse Jobs", href: "/jobs" },
  ];

  return (
    <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-6">
          <Link href="/candidate/dashboard" className="flex items-center space-x-3 group">
            <div className="w-8 h-8 rounded-xl bg-sky-500 flex items-center justify-center text-slate-950 font-black text-sm shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
              AH
            </div>
            <span className="font-black text-white text-lg tracking-tight">
              AuraHire <span className="text-gradient-cyan">Candidate</span>
            </span>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 pl-4 border-l border-slate-800">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-slate-900 text-sky-400 border border-slate-800 shadow-sm"
                      : "text-slate-400 hover:text-white hover:bg-slate-900/50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Identity & Logout */}
        <div className="flex items-center space-x-4">
          {user && (
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800">
              <div className="w-6 h-6 rounded-full bg-sky-500/20 border border-sky-500/40 text-sky-400 font-bold text-[10px] flex items-center justify-center font-mono">
                {user.full_name?.charAt(0) || "C"}
              </div>
              <span className="text-xs font-medium text-slate-200">{user.full_name || user.email}</span>
            </div>
          )}
          <button
            onClick={() => logout()}
            className="text-xs font-mono text-slate-400 hover:text-rose-400 transition-colors px-3 py-1.5 rounded-lg hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20"
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}
