"use client";

import React, { useState } from "react";

interface Member {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: string;
}

export default function TeamMembersPage() {
  const [members] = useState<Member[]>([
    {
      id: "1",
      full_name: "Primary Administrator",
      email: "admin@organization.com",
      role: "ORGANIZATION_ADMIN",
      status: "ACTIVE",
    },
  ]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("RECRUITER");

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    setInviteEmail("");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">Organization Team Members</h1>
            <p className="text-slate-400 text-xs mt-1">Manage team access, role assignments, and recruiter invitations.</p>
          </div>
        </div>

        {/* Invite Form */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-white mb-3">Invite Team Member</h2>
          <form onSubmit={handleInvite} className="flex flex-col sm:flex-row items-center gap-3">
            <label htmlFor="invite-email-input" className="sr-only">Colleague Email</label>
            <input
              id="invite-email-input"
              name="inviteEmail"
              autoComplete="email"
              type="email"
              required
              placeholder="colleague@organization.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 w-full"
            />
            <label htmlFor="invite-role-select" className="sr-only">Role</label>
            <select
              id="invite-role-select"
              name="inviteRole"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 w-full sm:w-auto"
            >
              <option value="RECRUITER">Recruiter</option>
              <option value="ORGANIZATION_ADMIN">Organization Admin</option>
            </select>
            <button
              type="submit"
              className="w-full sm:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
            >
              Send Invitation
            </button>
          </form>
        </div>

        {/* Members Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-900/80 uppercase tracking-wider">
                <th className="p-4">Name</th>
                <th className="p-4">Email</th>
                <th className="p-4">Role</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {members.map((m) => (
                <tr key={m.id} className="hover:bg-slate-900/50">
                  <td className="p-4 font-medium text-white">{m.full_name}</td>
                  <td className="p-4 text-slate-400">{m.email}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      {m.role}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {m.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
