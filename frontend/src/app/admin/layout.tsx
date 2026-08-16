"use client";

import React from "react";
import { PortalGuard } from "@/components/auth/PortalGuard";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <PortalGuard allowedPortals={["admin"]}>{children}</PortalGuard>;
}
