"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { exportRequisitionReportCSV, fetchRequisitionReport, RequisitionReport } from "@/lib/api";

export default function RecruiterRequisitionReportPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [report, setReport] = useState<RequisitionReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<boolean>(false);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);
    fetchRequisitionReport(jobId)
      .then((data) => {
        if (data) {
          setReport(data);
        } else {
          setError("Failed to load requisition report. Access denied or requisition not found.");
        }
      })
      .catch((err) => setError(err.message || "An unexpected error occurred."))
      .finally(() => setLoading(false));
  }, [jobId]);

  const handleExportCSV = async () => {
    if (!jobId) return;
    setExporting(true);
    try {
      const res = await exportRequisitionReportCSV(jobId);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `requisition_report_${jobId}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        alert("Failed to export report CSV.");
      }
    } catch (err: any) {
      alert(err.message || "CSV Export error.");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-8 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mb-4"></div>
        <p className="text-slate-400 font-medium">Generating Requisition Analytics Report...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-8 flex flex-col items-center justify-center">
        <div className="bg-red-950/40 border border-red-500/30 rounded-xl p-6 max-w-md text-center">
          <h2 className="text-xl font-bold text-red-400 mb-2">Report Error</h2>
          <p className="text-slate-300 text-sm mb-4">{error || "Requisition report unavailable."}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              REQUISITION ANALYTICS
            </span>
            <span
              className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                report.requisition_fill_status === "FILLED"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
              }`}
            >
              {report.requisition_fill_status === "FILLED" ? "REQUISITION FILLED" : "OPEN REQUISITION"}
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight mb-1">{report.title}</h1>
          <p className="text-slate-400 text-sm">
            {report.department || "General"} • {report.location || "Remote"} • {report.employment_type}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300">
            <span className="text-slate-500 mr-1.5">AI Governance:</span>
            <span className="text-indigo-400">AI ASSISTS. RECRUITER DECIDES.</span>
          </div>
          <button
            onClick={handleExportCSV}
            disabled={exporting}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm rounded-lg transition shadow-lg shadow-indigo-600/20 disabled:opacity-50 flex items-center gap-2"
          >
            {exporting ? "Exporting..." : "Export CSV Report"}
          </button>
        </div>
      </div>

      {/* Top Metrics Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Applications</p>
          <p className="text-2xl font-bold text-white">{report.total_applications}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Eligible</p>
          <p className="text-2xl font-bold text-emerald-400">{report.eligible_applications}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Reviewed</p>
          <p className="text-2xl font-bold text-indigo-400">{report.candidates_reviewed}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Advanced</p>
          <p className="text-2xl font-bold text-blue-400">{report.candidates_advanced}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Offers</p>
          <p className="text-2xl font-bold text-purple-400">{report.offers_extended}</p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Hired</p>
          <p className="text-2xl font-bold text-amber-400">{report.candidates_hired}</p>
        </div>
      </div>

      {/* Main Analytics Content Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Candidate Funnel & Conversion */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center justify-between">
            <span>Candidate Conversion Funnel</span>
            <span className="text-xs font-normal text-slate-400">Deterministic Calculations</span>
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-300">Applications → Eligible</span>
                <span className="text-emerald-400">{report.funnel_conversion.application_to_eligible_pct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${Math.min(100, report.funnel_conversion.application_to_eligible_pct)}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-300">Eligible → Top-K Ranked</span>
                <span className="text-indigo-400">{report.funnel_conversion.eligible_to_top_k_pct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, report.funnel_conversion.eligible_to_top_k_pct)}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-300">Top-K → Recruiter Reviewed</span>
                <span className="text-blue-400">{report.funnel_conversion.top_k_to_reviewed_pct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.min(100, report.funnel_conversion.top_k_to_reviewed_pct)}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-300">Reviewed → Advanced</span>
                <span className="text-purple-400">{report.funnel_conversion.reviewed_to_advanced_pct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${Math.min(100, report.funnel_conversion.reviewed_to_advanced_pct)}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-300">Offer Extended → Accepted</span>
                <span className="text-amber-400">{report.funnel_conversion.offer_to_accepted_pct}%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${Math.min(100, report.funnel_conversion.offer_to_accepted_pct)}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Time-to-Fill & Time-to-Hire Box */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-4">Lifecycle Time Metrics</h2>
            <div className="space-y-6">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Time To Fill</p>
                <p className="text-3xl font-extrabold text-indigo-400">
                  {report.time_to_fill_days !== null && report.time_to_fill_days !== undefined
                    ? `${report.time_to_fill_days} Days`
                    : "UNAVAILABLE"}
                </p>
                <p className="text-xs text-slate-500 mt-1">(placed_at - job.created_at)</p>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Time To Hire</p>
                <p className="text-3xl font-extrabold text-emerald-400">
                  {report.time_to_hire_days !== null && report.time_to_hire_days !== undefined
                    ? `${report.time_to_hire_days} Days`
                    : "UNAVAILABLE"}
                </p>
                <p className="text-xs text-slate-500 mt-1">(placed_at - application.submitted_at)</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-500 flex justify-between">
            <span>First Candidate: {report.time_to_first_candidate_days ?? "N/A"} d</span>
            <span>First Decision: {report.time_to_first_decision_days ?? "N/A"} d</span>
          </div>
        </div>

        {/* Score & Confidence Analytics */}
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6">
          <h2 className="text-lg font-bold text-white mb-4">Score Distribution</h2>
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Average</span>
              <span className="text-xl font-bold text-white">{report.score_analytics.average_score ?? "N/A"}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Median</span>
              <span className="text-xl font-bold text-white">{report.score_analytics.median_score ?? "N/A"}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Highest</span>
              <span className="text-xl font-bold text-emerald-400">{report.score_analytics.highest_score ?? "N/A"}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-slate-400 block">Lowest</span>
              <span className="text-xl font-bold text-red-400">{report.score_analytics.lowest_score ?? "N/A"}</span>
            </div>
          </div>

          <h3 className="text-sm font-semibold text-slate-300 mb-3">Confidence Breakdown</h3>
          <div className="flex gap-2">
            <div className="flex-1 bg-emerald-950/40 border border-emerald-500/30 p-2.5 rounded-lg text-center">
              <span className="text-xs text-emerald-400 font-bold block">HIGH</span>
              <span className="text-lg font-bold text-white">{report.score_analytics.confidence_distribution.HIGH}</span>
            </div>
            <div className="flex-1 bg-amber-950/40 border border-amber-500/30 p-2.5 rounded-lg text-center">
              <span className="text-xs text-amber-400 font-bold block">MEDIUM</span>
              <span className="text-lg font-bold text-white">{report.score_analytics.confidence_distribution.MEDIUM}</span>
            </div>
            <div className="flex-1 bg-red-950/40 border border-red-500/30 p-2.5 rounded-lg text-center">
              <span className="text-xs text-red-400 font-bold block">LOW</span>
              <span className="text-lg font-bold text-white">{report.score_analytics.confidence_distribution.LOW}</span>
            </div>
          </div>
        </div>

        {/* Recruiter Decisions vs AI Advisory */}
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6">
          <h2 className="text-lg font-bold text-white mb-4">Recruiter Decision Breakdown</h2>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-950/30 border border-blue-500/30 rounded-xl p-4 text-center">
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider block mb-1">ADVANCE</span>
              <span className="text-2xl font-bold text-white">{report.decision_analytics.decision_counts.ADVANCE}</span>
              <span className="text-xs text-blue-300/70 block mt-1">{report.decision_analytics.decision_rates_pct.advance_rate_pct}% of reviewed</span>
            </div>
            <div className="bg-red-950/30 border border-red-500/30 rounded-xl p-4 text-center">
              <span className="text-xs font-semibold text-red-400 uppercase tracking-wider block mb-1">REJECT</span>
              <span className="text-2xl font-bold text-white">{report.decision_analytics.decision_counts.REJECT}</span>
              <span className="text-xs text-red-300/70 block mt-1">{report.decision_analytics.decision_rates_pct.reject_rate_pct}% of reviewed</span>
            </div>
            <div className="bg-amber-950/30 border border-amber-500/30 rounded-xl p-4 text-center">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block mb-1">HOLD</span>
              <span className="text-2xl font-bold text-white">{report.decision_analytics.decision_counts.HOLD}</span>
              <span className="text-xs text-amber-300/70 block mt-1">{report.decision_analytics.decision_rates_pct.hold_rate_pct}% of reviewed</span>
            </div>
          </div>

          <div className="bg-slate-950 rounded-xl p-4 border border-slate-800">
            <p className="text-xs font-semibold text-slate-400 mb-1">AI Recommendation Distribution (Advisory Only)</p>
            <div className="flex gap-4 text-xs text-slate-300">
              <span>RECOMMEND: <strong>{report.decision_analytics.ai_recommendation_distribution.RECOMMEND}</strong></span>
              <span>REQUIRES_REVIEW: <strong>{report.decision_analytics.ai_recommendation_distribution.REQUIRES_REVIEW}</strong></span>
              <span>DO_NOT_RECOMMEND: <strong>{report.decision_analytics.ai_recommendation_distribution.DO_NOT_RECOMMEND}</strong></span>
            </div>
            <p className="text-[11px] text-slate-500 mt-2 font-mono">
              Note: {report.decision_analytics.ai_override_note}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
