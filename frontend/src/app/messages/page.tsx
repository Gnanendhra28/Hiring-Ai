"use client";

import React, { useState } from "react";
import { Send } from "lucide-react";

export default function MessagesPage() {
  const [threads, setThreads] = useState<any[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string>("");
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    async function loadThreads() {
      setLoading(true);
      try {
        const res = await fetch("/api/v1/candidate/applications");
        if (res.ok) {
          const apps = await res.json();
          const items = await Promise.all(
            apps.map(async (a: any, idx: number) => {
              let jobTitle = "Software Engineering Requisition";
              let orgName = "Enterprise Partner";
              try {
                const jRes = await fetch(`/api/v1/jobs/${a.job_id}`);
                if (jRes.ok) {
                  const jData = await jRes.json();
                  jobTitle = jData.title || jobTitle;
                  orgName = jData.organization_name || orgName;
                }
              } catch {}

              const isShortlisted = a.status === "SHORTLISTED" || a.status === "INTERVIEW" || a.status === "SELECTED";
              return {
                id: `thread-${a.id}`,
                recruiterName: "Hiring Team",
                organization: orgName,
                role: jobTitle,
                lastMessage: isShortlisted 
                  ? `Your application for ${jobTitle} has been shortlisted by the recruiting team.`
                  : `Your application for ${jobTitle} was received and is under review.`,
                time: new Date(a.submitted_at || Date.now()).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
                unread: isShortlisted ? 1 : 0,
                messages: [
                  {
                    id: `m-${a.id}-1`,
                    sender: "recruiter",
                    text: `Hello! Thank you for applying to the ${jobTitle} role at ${orgName}.`,
                    time: new Date(a.submitted_at || Date.now()).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
                  },
                  {
                    id: `m-${a.id}-2`,
                    sender: "recruiter",
                    text: isShortlisted 
                      ? `Great news! Your qualifications and skill matches meet our benchmark. Our engineering team is reviewing your profile.`
                      : `Our AI recruitment engine has verified your application submission. We will notify you here once the stage updates.`,
                    time: new Date(a.submitted_at || Date.now()).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
                  },
                ],
              };
            })
          );
          setThreads(items);
          if (items.length > 0) {
            setActiveThreadId(items[0].id);
          }
        }
      } catch (err) {
        console.error("Error loading messaging threads:", err);
      } finally {
        setLoading(false);
      }
    }
    loadThreads();
  }, []);

  const activeThread = threads.find((t) => t.id === activeThreadId) || threads[0];

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;
    activeThread.messages.push({
      id: `msg-${Date.now()}`,
      sender: "candidate",
      text: inputMessage.trim(),
      time: "Just now",
    });
    setInputMessage("");
  };

  return (
    <div className="h-page space-y-6">
      {/* Header */}
      <section className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <p className="page-eyebrow">Recruiter Communications</p>
          <h1 className="page-title">Messages &amp; Discussions</h1>
          <p className="page-subtitle">Direct candidate-recruiter messaging for interview scheduling and evaluation updates.</p>
        </div>
      </section>

      {/* Messages Layout Grid */}
      <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)] h-[600px]">
        {/* Left Threads Sidebar */}
        <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col space-y-2 overflow-y-auto">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1">
            Active Conversations
          </p>
          {loading ? (
            <p className="text-xs text-slate-400 p-3">Loading conversations...</p>
          ) : threads.length === 0 ? (
            <p className="text-xs text-slate-400 p-3">No active message threads yet.</p>
          ) : (
            threads.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveThreadId(t.id)}
                className={`p-3 rounded-xl text-left transition-all flex flex-col gap-1.5 ${
                  activeThreadId === t.id
                    ? "bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-900"
                    : "hover:bg-slate-50 dark:hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 dark:text-white text-xs">
                    {t.recruiterName}
                  </span>
                  <span className="text-[10px] text-slate-400">{t.time}</span>
                </div>
                <span className="text-[11px] text-indigo-600 dark:text-indigo-400 font-semibold">
                  {t.organization}
                </span>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-1">
                  {t.lastMessage}
                </p>
              </button>
            ))
          )}
        </div>

        {/* Right Active Chat Window */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col justify-between overflow-hidden">
          {activeThread ? (
            <>
              {/* Thread Header */}
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/80 dark:bg-slate-900/80">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-bold grid place-items-center text-sm">
                    {activeThread.recruiterName?.[0] || "H"}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                      {activeThread.recruiterName}
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                      {activeThread.role} • {activeThread.organization}
                    </p>
                  </div>
                </div>
              </div>

              {/* Messages Stream */}
              <div className="p-6 space-y-4 overflow-y-auto flex-1 bg-slate-50/50 dark:bg-slate-950/40">
                {activeThread.messages?.map((m: any) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${
                      m.sender === "candidate" ? "items-end" : "items-start"
                    }`}
                  >
                    <div
                      className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed ${
                        m.sender === "candidate"
                          ? "bg-indigo-600 text-white rounded-br-none shadow-xs"
                          : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-bl-none shadow-xs font-medium"
                      }`}
                    >
                      {m.text}
                    </div>
                    <span className="text-[10px] text-slate-400 mt-1 px-1">
                      {m.time}
                    </span>
                  </div>
                ))}
              </div>

              {/* Chat Input */}
              <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex gap-2">
                <input
                  className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none focus:border-indigo-500"
                  placeholder="Type a message to the hiring team..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                />
                <button
                  onClick={handleSendMessage}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 flex items-center gap-1.5 transition-all"
                >
                  <Send size={15} /> Send
                </button>
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-slate-400 text-xs my-auto">
              Select or start an application to begin direct communication with the hiring team.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
