"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";
import { Bell, BriefcaseBusiness, ChevronDown, CircleUserRound, LayoutDashboard, MessageCircle, Search, Settings, Sparkles, UserRound, UsersRound } from "lucide-react";

export function CandidateNavbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { label: "Home", href: "/candidate/dashboard", icon: LayoutDashboard }, { label: "Jobs", href: "/jobs", icon: BriefcaseBusiness }, { label: "Applications", href: "/candidate/applications", icon: CircleUserRound }, { label: "Network", href: "/network", icon: UsersRound }, { label: "AI Career", href: "/career", icon: Sparkles }, { label: "Messages", href: "/messages", icon: MessageCircle },
  ];

  return (
    <>
    <header className="hiring-header">
      <div className="hiring-header-inner">
        {/* Brand */}
        <div className="flex items-center space-x-6">
          <Link href="/candidate/dashboard" className="brand">
            <span className="brand-mark"><Sparkles size={17}/></span><span>Hiring<span>AI</span></span>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden">
            {navItems.map((item) => <Link key={item.href} href={item.href}>{item.label}</Link>)}
          </nav>
        </div>

        {/* User Identity & Logout */}
        <label className="global-search"><Search size={17}/><input aria-label="Global search" placeholder="Search jobs, companies, people..."/></label>
        <div className="header-actions">
          <button aria-label="Notifications" className="icon-button"><Bell size={19}/><i/></button><Link aria-label="Messages" href="/messages" className="icon-button"><MessageCircle size={19}/></Link>
          <button onClick={() => logout()} className="avatar-button"><span>{user?.full_name?.charAt(0).toUpperCase() || "G"}</span><ChevronDown size={15}/></button>
        </div>
      </div>
    </header>
    <aside className="hiring-sidebar"><nav>{navItems.map(({label,href,icon:Icon})=><Link key={href} href={href} className={pathname===href?"nav-link active":"nav-link"}><Icon size={18}/><span>{label}</span></Link>)}</nav><div className="sidebar-bottom"><Link href="/candidate/profile" className="nav-link"><UserRound size={18}/><span>Profile</span></Link><Link href="/settings" className="nav-link"><Settings size={18}/><span>Settings</span></Link><div className="ai-side-card"><Sparkles size={16}/><strong>Your profile is 82% ready</strong><Link href="/candidate/profile">Improve profile</Link></div></div></aside>
    <nav className="mobile-nav">{[navItems[0],navItems[1],navItems[4],navItems[5],{label:"Profile",href:"/candidate/profile",icon:UserRound}].map(({label,href,icon:Icon})=><Link key={href} href={href} className={pathname===href?"active":""}><Icon size={20}/><span>{label}</span></Link>)}</nav>
    </>
  );
}
