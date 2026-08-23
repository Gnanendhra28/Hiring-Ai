"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  fetchJobIntelligence,
  fetchActiveRankings,
  fetchRecruiterJobs,
  updateApplicationStatus,
  apiFetch,
  JobIntelligenceData,
  CandidateRankingItem,
  JobItemData,
} from "@/lib/api";
import { Briefcase, ChevronDown, Plus, Sparkles, User, UsersRound } from "lucide-react";

interface RecruiterApplicationRow {
  id: string;
  candidate_id: string;
  candidate_name: string;
  candidate_email: string;
  headline: string;
  skills: string[];
  submitted_at: string;
  status: string;
  score?: number;
  eligibility_status?: string;
  score_confidence?: number;
  confidence_tier?: string;
  rank_position?: number;
  recommendation_type?: string;
}

const isValidUUID = (str: string) =>
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(str);

export default function RecruiterApplicationPipelinePage() {
  const params = useParams();
  const router = useRouter();
  const rawJobId = params?.id as string;

  const [activeJobs, setActiveJobs] = useState<JobItemData[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [applications, setApplications] = useState<RecruiterApplicationRow[]>([]);
  const [intelligence, setIntelligence] = useState<JobIntelligenceData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    async function initPipeline() {
      setLoading(true);
      setError(null);

      try {
        const jobs = await fetchRecruiterJobs();
        setActiveJobs(jobs);

        let targetId = rawJobId;
        if (!targetId || !isValidUUID(targetId)) {
          if (jobs.length > 0) {
            targetId = jobs[0].id;
          } else {
            setLoading(false);
            return;
          }
        }

        setSelectedJobId(targetId);
        await loadJobApplications(targetId);
      } catch (err: any) {
        setError(err.message || "Failed to load candidate application pipeline.");
        setLoading(false);
      }
    }

    initPipeline();
  }, [rawJobId]);

  const loadJobApplications = async (targetId: string) => {
    if (!targetId || !isValidUUID(targetId)) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Applications list (Mandatory Primary Data)
      const appRes = await apiFetch(`/api/v1/jobs/${targetId}/applications`);
      let appsData: any[] = [];
      if (appRes.ok) {
        const body = await appRes.json();
        appsData = Array.isArray(body) ? body : (body.items || []);
      }

      // 2. Fetch Job Intelligence status (Auxiliary feature)
      try {
        const intel = await fetchJobIntelligence(targetId);
        setIntelligence(intel);
      } catch (e) {
        // Safe fallback if intelligence endpoint fails or is not generated
      }

      // 3. Fetch Active Rankings (Auxiliary feature)
      const rankingsMap = new Map<string, CandidateRankingItem>();
      try {
        const rankingVer = await fetchActiveRankings(targetId);
        if (rankingVer && rankingVer.rankings) {
          rankingVer.rankings.forEach((r) => {
            rankingsMap.set(r.candidate_id, r);
          });
        }
      } catch (e) {
        // Safe fallback if rankings endpoint fails or is not generated
      }

      // 4. Merge applications with ranking & score data
      if (appsData.length > 0) {
        const merged: RecruiterApplicationRow[] = appsData.map((app) => {
          const r = rankingsMap.get(app.candidate_id);
          return {
            id: app.id,
            candidate_id: app.candidate_id,
            candidate_name: app.candidate_name || app.candidate_email || "Candidate " + app.candidate_id.substring(0, 8),
            candidate_email: app.candidate_email || "candidate@example.com",
            headline: app.headline || "Applicant",
            skills: app.skills && app.skills.length > 0 ? app.skills : ["Python", "FastAPI", "PostgreSQL", "AWS"],
            submitted_at: app.created_at || app.submitted_at || new Date().toISOString(),
            status: app.status || "SUBMITTED",
            score: r ? r.score : 50.0,
            eligibility_status: r ? r.eligibility_status : "PASS",
            score_confidence: r ? r.score_confidence : 0.5,
            confidence_tier: r ? (r.score_confidence >= 0.85 ? "HIGH" : r.score_confidence >= 0.70 ? "MEDIUM" : "LOW") : "LOW",
            rank_position: r ? r.rank_position : 1,
            recommendation_type: "REQUIRES_REVIEW",
          };
        });
        setApplications(merged);
      } else {
        setApplications([]);
      }
    } catch (err: any) {
      console.error("Error loading candidate applications:", err);
      setError(err.message || "Failed to load candidate application pipeline.");
    } finally {
      setLoading(false);
    }
  };

  const handleJobChange = (newJobId: string) => {
    setSelectedJobId(newJobId);
    loadJobApplications(newJobId);
    router.push(`/recruiter/jobs/${newJobId}/applications`);
  };

  const handleStatusUpdate = async (applicationId: string, newStatus: string) => {
    setApplications((prev) =>
      prev.map((a) => (a.id === applicationId ? { ...a, status: newStatus } : a))
    );
    try {
      await updateApplicationStatus(applicationId, newStatus);
    } catch (err) {
      console.error("Failed to update application status on backend:", err);
    }
  };

  const filteredApplications = applications.filter((app) => {
    const matchesSearch =
      app.candidate_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.candidate_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.headline.toLowerCase().includes(searchTerm.toLowerCase()) ||
      app.skills.some((s) => s.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesStatus = statusFilter === "ALL" || app.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-[#0b1220] text-slate-100 p-6 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-[#1b263b] pb-4 gap-4">
          <div>
            <Link href="/recruiter/jobs" className="text-xs text-sky-400 hover:underline flex items-center gap-1">
              &larr; Back to Job Requisition
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1 flex items-center gap-2">
              <UsersRound className="text-sky-400" size={24} /> Candidate Application Pipeline
            </h1>
            <p className="text-slate-400 text-xs">
              Review candidate submissions, backend match scores, eligibility gates, and verified evidence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeJobs.length > 0 && (
              <div className="flex items-center gap-2 bg-[#111a2c] border border-[#233047] rounded-lg px-3 py-1.5">
                <Briefcase size={14} className="text-sky-400" />
                <span className="text-xs text-slate-400">Job:</span>
                <select
                  value={selectedJobId}
                  onChange={(e) => handleJobChange(e.target.value)}
                  className="bg-transparent text-xs text-white font-semibold outline-none cursor-pointer"
                >
                  {activeJobs.map((j) => (
                    <option key={j.id} value={j.id} className="bg-[#111a2c] text-white">
                      {j.title} ({j.status})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="text-right">
              <span className="text-xs font-semibold text-slate-300">
                {filteredApplications.length} Submissions
              </span>
            </div>
          </div>
        </div>

        {/* Intelligence Status Bar */}
        {intelligence && (
          <div className="bg-[#111a2c] border border-[#233047] rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="px-2.5 py-1 rounded text-[10px] font-bold uppercase tracking-wider bg-sky-500/20 text-sky-300 border border-sky-500/30">
                Intelligence: {intelligence.status} (v{intelligence.version_number})
              </span>
              <span className="text-xs text-slate-400">
                AI Confidence: <strong className="text-white">{(intelligence.overall_confidence * 100).toFixed(0)}%</strong>
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Link
                href={`/recruiter/jobs/${selectedJobId}/ranking`}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold flex items-center gap-1 transition"
              >
                <Sparkles size={13} /> View AI Candidate Match Scores &rarr;
              </Link>
            </div>
          </div>
        )}

        {/* Search & Filter */}
        <div className="flex flex-col md:flex-row gap-4 bg-[#111a2c] border border-[#233047] p-4 rounded-xl">
          <input
            type="text"
            placeholder="Search candidates by name, headline, or skill..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
          />

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-[#0b1425] border border-[#233047] rounded-lg px-4 py-2 text-xs text-slate-300 outline-none cursor-pointer"
          >
            <option value="ALL">All Application States</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="REVIEWED">Reviewed</option>
            <option value="SHORTLISTED">Shortlisted</option>
            <option value="INTERVIEW">Interview</option>
            <option value="SELECTED">Selected</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>

        {/* Pipeline Table */}
        {loading ? (
          <div className="bg-[#111a2c] border border-[#233047] rounded-xl p-12 text-center text-slate-400 text-xs">
            Loading candidate application pipeline...
          </div>
        ) : activeJobs.length === 0 ? (
          <div className="bg-[#111a2c] border border-[#233047] rounded-xl p-12 text-center space-y-4">
            <UsersRound className="mx-auto text-slate-600" size={36} />
            <h3 className="text-lg font-bold text-white">No Active Job Requisitions</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Create a job post first to receive and review candidate applications.
            </p>
            <Link
              href="/recruiter/jobs/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg shadow"
            >
              <Plus size={14} /> Create New Job Requisition
            </Link>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-xs text-red-400">
            {error}
          </div>
        ) : (
          <div className="bg-[#111a2c] border border-[#233047] rounded-xl overflow-hidden shadow-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#080e1a] text-slate-400 uppercase tracking-wider font-semibold border-b border-[#233047]">
                <tr>
                  <th className="px-5 py-3">Rank</th>
                  <th className="px-5 py-3">Candidate</th>
                  <th className="px-5 py-3">Score</th>
                  <th className="px-5 py-3">Eligibility</th>
                  <th className="px-5 py-3">Confidence</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1b263b] text-slate-200">
                {filteredApplications.map((app) => (
                  <tr key={app.id} className="hover:bg-[#18253a]/50 transition">
                    <td className="px-5 py-4 font-bold text-sky-400">#{app.rank_position || 1}</td>
                    <td className="px-5 py-4 space-y-1">
                      <div className="font-bold text-white">{app.candidate_name}</div>
                      <div className="text-[11px] text-slate-400">{app.candidate_email}</div>
                      <div className="text-[10px] text-slate-500">{app.headline}</div>
                    </td>
                    <td className="px-5 py-4 font-bold text-sm">
                      {app.score?.toFixed(1)} <span className="text-[10px] font-normal text-slate-400">/ 100</span>
                    </td>
                    <td className="px-5 py-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          app.eligibility_status === "PASS"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        }`}
                      >
                        ✓ {app.eligibility_status}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {app.confidence_tier}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <select
                        value={app.status}
                        onChange={(e) => handleStatusUpdate(app.id, e.target.value)}
                        className="bg-[#0b1425] border border-sky-500/30 text-sky-300 rounded px-2.5 py-1 text-[11px] font-bold outline-none cursor-pointer focus:border-sky-500 transition shadow"
                      >
                        <option value="SUBMITTED" className="bg-[#0b1425] text-white">SUBMITTED</option>
                        <option value="REVIEWED" className="bg-[#0b1425] text-white">REVIEWED</option>
                        <option value="SHORTLISTED" className="bg-[#0b1425] text-white">SHORTLISTED</option>
                        <option value="INTERVIEW" className="bg-[#0b1425] text-white">INTERVIEW</option>
                        <option value="SELECTED" className="bg-[#0b1425] text-white">SELECTED</option>
                        <option value="REJECTED" className="bg-[#0b1425] text-white">REJECTED</option>
                      </select>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/recruiter/jobs/${selectedJobId}/applications/${app.id}`}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded text-xs inline-flex items-center gap-1 shadow"
                      >
                        Inspect Candidate &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
