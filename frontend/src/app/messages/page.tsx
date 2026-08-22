"use client";

import React, { useState } from "react";
import { CheckCheck, MessageSquare, Send, Sparkles, User } from "lucide-react";

export default function MessagesPage() {
  const [activeThreadId, setActiveThreadId] = useState("thread-1");
  const [inputMessage, setInputMessage] = useState("");

  const threads = [
    {
      id: "thread-1",
      recruiterName: "Santhosh Kumar",
      organization: "Enterprise Hiring AI",
      role: "Lead Recruiter",
      lastMessage: "Hi Gnanendhra! We reviewed your profile for the Generative AI Engineer position...",
      time: "10:45 AM",
      unread: 1,
      messages: [
        {
          id: "m1",
          sender: "recruiter",
          text: "Hello Gnanendhra! Thank you for applying to the Generative AI Engineer requisition at Enterprise Hiring AI.",
          time: "10:30 AM",
        },
        {
          id: "m2",
          sender: "recruiter",
          text: "We reviewed your profile and RAG architecture projects, and we would love to schedule a technical discussion with our engineering lead.",
          time: "10:45 AM",
        },
      ],
    },
    {
      id: "thread-2",
      recruiterName: "Ananya Sharma",
      organization: "Aster Labs",
      role: "AI Acquisition Lead",
      lastMessage: "Looking forward to receiving your updated GitHub portfolio link.",
      time: "Yesterday",
      unread: 0,
      messages: [
        {
          id: "m3",
          sender: "recruiter",
          text: "Hi Gnanendhra, please share your updated GitHub repository link for the Python backend evaluation.",
          time: "Yesterday 4:15 PM",
        },
        {
          id: "m4",
          sender: "candidate",
          text: "Sure! I have updated my profile with the repository link.",
          time: "Yesterday 5:00 PM",
        },
      ],
    },
  ];

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
        <div className="h-card p-3 flex flex-col space-y-2 overflow-y-auto">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1">
            Active Conversations
          </p>
          {threads.map((t) => (
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
          ))}
        </div>

        {/* Right Active Chat Window */}
        <div className="h-card flex flex-col justify-between overflow-hidden">
          {/* Thread Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-indigo-600 text-white font-bold grid place-items-center text-sm">
                {activeThread.recruiterName[0]}
              </div>
              <div>
                <h3 className="font-bold text-slate-900 dark:text-white text-sm">
                  {activeThread.recruiterName}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {activeThread.role} • {activeThread.organization}
                </p>
              </div>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="p-6 space-y-4 overflow-y-auto flex-1 bg-slate-50/30 dark:bg-slate-950/30">
            {activeThread.messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${
                  m.sender === "candidate" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed ${
                    m.sender === "candidate"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-none shadow-xs"
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
              className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none focus:border-indigo-500"
              placeholder="Type your response to the recruiter..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
            />
            <button onClick={handleSendMessage} className="h-btn px-4">
              <Send size={15} /> Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
