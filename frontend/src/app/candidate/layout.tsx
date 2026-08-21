"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { PortalGuard } from "@/components/auth/PortalGuard";
import { CandidateNavbar } from "@/components/candidate/CandidateNavbar";

export default function CandidateLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = Boolean(pathname && (pathname.includes("/login") || pathname.includes("/signup")));

  if (isAuthPage) {
    return <PortalGuard allowedPortals={["candidate"]}>{children}</PortalGuard>;
  }

  return (
    <PortalGuard allowedPortals={["candidate"]}>
      <div className="hiring-shell">
        <CandidateNavbar />
        <main className="hiring-main">{children}</main>
      </div>
    </PortalGuard>
  );
}
