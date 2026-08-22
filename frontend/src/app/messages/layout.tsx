"use client";

import React from "react";
import { CandidateNavbar } from "@/components/candidate/CandidateNavbar";

export default function MessagesLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="hiring-shell">
      <CandidateNavbar />
      <main className="hiring-main">{children}</main>
    </div>
  );
}
