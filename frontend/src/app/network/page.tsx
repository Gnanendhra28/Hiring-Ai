"use client";

import React, { useState } from "react";
import { Building2, Check, MapPin, Search, Sparkles, UserPlus, Users } from "lucide-react";

export default function NetworkPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [connections, setConnections] = useState<string[]>([]);

  const connectionsList = [
    {
      id: "net-1",
      name: "Dr. Ananya Sharma",
      role: "Lead AI Researcher @ Aster Labs",
      location: "Bengaluru, India",
      mutual: 14,
      skills: ["Generative AI", "LLM Fine-tuning", "PyTorch"],
    },
    {
      id: "net-2",
      name: "Santhosh Kumar",
      role: "Principal Talent Acquisition @ Enterprise Tech",
      location: "Remote · India",
      mutual: 22,
      skills: ["Executive Hiring", "AI Talent", "Tech Recruitment"],
    },
    {
      id: "net-3",
      name: "Rahul Verma",
      role: "Staff Machine Learning Engineer @ Nexus AI",
      location: "Pune, India",
      mutual: 9,
      skills: ["RAG Architecture", "FastAPI", "Vector DBs"],
    },
  ];

  const handleConnect = (id: string) => {
    if (!connections.includes(id)) {
      setConnections([...connections, id]);
    }
  };

  const filtered = connectionsList.filter(
    (c) =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-page space-y-6">
      {/* Header */}
      <section className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow">Professional Network</p>
          <h1 className="page-title">AI &amp; Tech Network</h1>
          <p className="page-subtitle">Connect with top AI researchers, recruiters, and engineering leaders in your field.</p>
        </div>
      </section>

      {/* Search Bar */}
      <div className="h-card p-4">
        <label className="flex items-center gap-3">
          <Search size={18} className="text-slate-400" />
          <input
            className="w-full bg-transparent text-xs sm:text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none"
            placeholder="Search connections by name, company, or technical role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </label>
      </div>

      {/* Network Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((person) => {
          const isConnected = connections.includes(person.id);
          return (
            <article key={person.id} className="h-card p-6 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-950/60 font-bold text-indigo-700 dark:text-indigo-300 grid place-items-center text-lg">
                    {person.name[0]}
                  </div>
                  <span className="h-chip bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-semibold text-[10px]">
                    {person.mutual} Mutual Connections
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">
                    {person.name}
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                    {person.role}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1">
                    <MapPin size={12} /> {person.location}
                  </p>
                </div>

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {person.skills.map((s) => (
                    <span key={s} className="h-chip">
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={() => handleConnect(person.id)}
                disabled={isConnected}
                className={`w-full py-2.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                  isConnected
                    ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 cursor-default"
                    : "h-btn"
                }`}
              >
                {isConnected ? (
                  <>
                    <Check size={15} /> Connection Requested
                  </>
                ) : (
                  <>
                    <UserPlus size={15} /> Connect
                  </>
                )}
              </button>
            </article>
          );
        })}
      </div>
    </div>
  );
}
