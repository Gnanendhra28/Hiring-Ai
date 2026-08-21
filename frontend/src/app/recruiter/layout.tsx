"use client";

import React from "react";
import { PortalGuard } from "@/components/auth/PortalGuard";
import { RecruiterConsoleNav } from "@/components/hiringai/RecruiterConsoleNav";

export default function RecruiterLayout({ children }: { children: React.ReactNode }) {
  return <PortalGuard allowedPortals={["recruiter"]}><div className="command-shell"><RecruiterConsoleNav/><main className="command-main">{children}</main></div></PortalGuard>;
}
