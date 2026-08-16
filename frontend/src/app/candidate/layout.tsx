"use client";

import React from "react";
import { PortalGuard } from "@/components/auth/PortalGuard";

export default function CandidateLayout({ children }: { children: React.ReactNode }) {
  return <PortalGuard allowedPortals={["candidate"]}>{children}</PortalGuard>;
}
