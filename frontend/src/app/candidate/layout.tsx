"use client";

import React from "react";
import { PortalGuard } from "@/components/auth/PortalGuard";
import { CandidateNavbar } from "@/components/candidate/CandidateNavbar";

export default function CandidateLayout({ children }: { children: React.ReactNode }) {
  return (
    <PortalGuard allowedPortals={["candidate"]}>
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-sky-500 selection:text-white flex flex-col relative overflow-x-hidden">
        {/* Ambient background glow & grid */}
        <div className="fixed inset-0 bg-hero-glow pointer-events-none opacity-30 z-0" />
        <div className="fixed inset-0 bg-grid-pattern opacity-10 pointer-events-none z-0" />

        <CandidateNavbar />
        <main className="flex-1 relative z-10">{children}</main>

        <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500 font-mono relative z-10">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>© 2026 AuraHire AI Enterprise • Candidate Portal</span>
            <span className="text-emerald-400 font-semibold">✓ AI ASSISTS. RECRUITER DECIDES.</span>
          </div>
        </footer>
      </div>
    </PortalGuard>
  );
}
