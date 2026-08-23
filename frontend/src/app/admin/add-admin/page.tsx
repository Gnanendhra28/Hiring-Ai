"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CheckCircle2, ShieldCheck, UserPlus, Users } from "lucide-react";
import { createAdminAccount } from "@/lib/api";

export default function AddAdminPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (!fullName || !email || !password) {
      setMessage({ text: "Please fill in all required admin account fields.", isError: true });
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await createAdminAccount(fullName, email, password);
      if (res.success) {
        setMessage({ text: res.message, isError: false });
        setFullName("");
        setEmail("");
        setPassword("");
      } else {
        setMessage({ text: res.message, isError: true });
      }
    } catch (err: any) {
      setMessage({ text: err.message || "Failed to provision Admin account.", isError: true });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-2xl">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck size={12} /> Platform Admin Security Control
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Provision New Platform Admin
            </h1>
            <p className="text-slate-400 text-xs md:text-sm max-w-xl">
              Create a new Platform Admin account with full authorization to verify employers, approve job posts, and manage platform compliance.
            </p>
          </div>

          <button
            onClick={() => router.push("/admin/dashboard")}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            &larr; Admin Console
          </button>
        </div>

        {/* Add Admin Form Card */}
        <div className="bg-[#111a2c] border border-[#233047] rounded-2xl p-8 shadow-xl max-w-2xl mx-auto space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 font-bold">
              <UserPlus size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Platform Admin Credentials</h2>
              <p className="text-xs text-slate-400">Enter the identity details and password for the new admin account.</p>
            </div>
          </div>

          {message && (
            <div
              className={`p-4 rounded-xl text-xs font-semibold flex items-start gap-2 ${
                message.isError
                  ? "bg-rose-500/10 border border-rose-500/30 text-rose-400"
                  : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
              }`}
            >
              <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
              <span>{message.text}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="admin-full-name-input" className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
                Admin Full Name
              </label>
              <input
                id="admin-full-name-input"
                name="fullName"
                autoComplete="name"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Gnanendhra Joy"
                className="w-full px-4 py-3 rounded-xl bg-[#080e1a] border border-[#233047] text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm transition-all"
              />
            </div>

            <div>
              <label htmlFor="admin-email-input" className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
                Admin Work Email
              </label>
              <input
                id="admin-email-input"
                name="email"
                autoComplete="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. mattag@iitbhilai.ac.in"
                className="w-full px-4 py-3 rounded-xl bg-[#080e1a] border border-[#233047] text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm transition-all"
              />
            </div>

            <div>
              <label htmlFor="admin-password-input" className="block text-xs font-mono uppercase text-slate-400 mb-1.5">
                Account Password
              </label>
              <div className="relative">
                <input
                  id="admin-password-input"
                  name="password"
                  autoComplete="new-password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-[#080e1a] border border-[#233047] text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 text-sm pr-14 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3.5 text-slate-400 hover:text-white text-xs font-mono"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 font-bold text-white shadow-lg text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2 mt-4"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  <span>Provisioning Account...</span>
                </>
              ) : (
                <>
                  <UserPlus size={16} />
                  <span>Provision Platform Admin Account</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
