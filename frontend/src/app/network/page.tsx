"use client";

import React, { useState } from "react";
import { Check, MapPin, Search, UserPlus } from "lucide-react";

export default function NetworkPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [connections, setConnections] = useState<string[]>([]);
  const [connectionsList, setConnectionsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    async function loadNetwork() {
      setLoading(true);
      try {
        const res = await fetch("/api/v1/jobs?public_only=true");
        if (res.ok) {
          const data = await res.json();
          const items = data.items || [];
          const list = items.map((j: any, idx: number) => ({
            id: `net-${j.id}`,
            name: `${j.organization_name || "Enterprise Partner"} Hiring Team`,
            role: `Technical Lead • ${j.title}`,
            location: j.location || "Bengaluru · India",
            mutual: 8 + (idx * 3) % 15,
            skills: j.skills?.length ? j.skills : ["AI Engineering", "Cloud", "Distributed Systems"],
          }));
          setConnectionsList(list);
        }
      } catch (err) {
        console.error("Failed loading network:", err);
      } finally {
        setLoading(false);
      }
    }
    loadNetwork();
  }, []);

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
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
        <label className="flex items-center gap-3">
          <Search size={18} className="text-slate-400 shrink-0" />
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
            <article
              key={person.id}
              className="p-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-950/60 font-bold text-indigo-700 dark:text-indigo-300 grid place-items-center text-lg">
                    {person.name[0]}
                  </div>
                  <span className="px-2.5 py-1 rounded-md bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-bold text-[10px]">
                    {person.mutual} Mutual Connections
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">
                    {person.name}
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 font-medium">
                    {person.role}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1">
                    <MapPin size={12} /> {person.location}
                  </p>
                </div>

                <div className="flex flex-wrap gap-1.5 pt-1">
                  {person.skills.map((s: string) => (
                    <span
                      key={s}
                      className="px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium"
                    >
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
                    : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20"
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
