"use client";

import React from "react";
import { PortalGuard } from "@/components/auth/PortalGuard";

export default function RecruiterLayout({ children }: { children: React.ReactNode }) {
  return <PortalGuard allowedPortals={["recruiter"]}>{children}</PortalGuard>;
}
