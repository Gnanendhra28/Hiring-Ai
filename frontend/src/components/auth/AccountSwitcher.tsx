"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "./AuthContext";
import { Users, Check, Plus, LogOut, ShieldCheck, Briefcase, UserRound, ChevronDown } from "lucide-react";

export function AccountSwitcher() {
  const { user, savedAccounts, switchAccount, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user && (!savedAccounts || savedAccounts.length === 0)) {
    return null;
  }

  const currentEmail = user?.email?.toLowerCase() || "";
  const otherAccounts = (savedAccounts || []).filter((a) => a.email.toLowerCase() !== currentEmail);

  return (
    <div ref={dropdownRef} className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-semibold shadow transition-all"
        title="Switch or Manage Accounts"
      >
        <Users size={14} className="text-sky-400" />
        <span className="max-w-[120px] truncate">{user?.email || "Switch Account"}</span>
        <ChevronDown size={13} className={`text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl p-2.5 z-[100] text-xs space-y-2 animate-in fade-in zoom-in-95 duration-150">
          {/* Active Account Info */}
          {user && (
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider">Active Account</span>
                <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400">
                  <Check size={11} /> Current
                </span>
              </div>
              <p className="font-bold text-white mt-1 truncate">{user.full_name || "User"}</p>
              <p className="text-slate-300 font-mono text-[11px] truncate">{user.email}</p>
              <span className="inline-block mt-1.5 px-2 py-0.5 rounded-md bg-slate-800 text-[10px] font-semibold text-slate-300">
                {user.is_platform_admin ? "Platform Admin" : "User / Member"}
              </span>
            </div>
          )}

          {/* Other Saved Accounts */}
          {otherAccounts.length > 0 && (
            <div className="space-y-1 pt-1 border-t border-slate-800">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider px-2 block">
                Switch Account
              </span>
              {otherAccounts.map((account) => (
                <div
                  key={account.email}
                  className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-800/80 transition-colors group cursor-pointer"
                  onClick={() => {
                    setIsOpen(false);
                    switchAccount(account.email);
                  }}
                >
                  <div className="overflow-hidden mr-2">
                    <div className="flex items-center gap-1.5">
                      {account.role === "PLATFORM_ADMIN" ? (
                        <ShieldCheck size={13} className="text-amber-400 shrink-0" />
                      ) : account.role === "RECRUITER" || account.role === "ORGANIZATION_ADMIN" ? (
                        <Briefcase size={13} className="text-sky-400 shrink-0" />
                      ) : (
                        <UserRound size={13} className="text-emerald-400 shrink-0" />
                      )}
                      <p className="font-semibold text-slate-200 truncate">{account.fullName || account.email}</p>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono truncate">{account.email}</p>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-sky-300 group-hover:bg-sky-500 group-hover:text-slate-950 transition-colors shrink-0">
                    Switch
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Quick Actions */}
          <div className="pt-2 border-t border-slate-800 space-y-1">
            <Link
              href="/login"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 w-full p-2 rounded-xl text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <Plus size={14} className="text-sky-400" />
              <span>Sign in to another account</span>
            </Link>

            <button
              onClick={() => {
                setIsOpen(false);
                logout();
              }}
              className="flex items-center gap-2 w-full p-2 rounded-xl text-rose-400 hover:bg-rose-950/40 transition-colors text-left"
            >
              <LogOut size={14} />
              <span>Log out of current account</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
