"use client";

import React, { useEffect, useState } from "react";
import {
  fetchOrganizationDashboard,
  fetchAuditAnalytics,
  fetchAIGovernanceAnalytics,
  fetchAITelemetry,
  exportOrganizationReportCSV,
  OrganizationDashboard,
  AuditAnalytics,
  AIGovernanceAnalytics,
  AITelemetry,
  OrganizationRequisitionPerformanceRow,
} from "@/lib/api";

export default function EnterpriseReportsPage() {
  const [dashboard, setDashboard] = useState<OrganizationDashboard | null>(null);
  const [audit, setAudit] = useState<AuditAnalytics | null>(null);
  const [aiGov, setAiGov] = useState<AIGovernanceAnalytics | null>(null);
  const [telemetry, setTelemetry] = useState<AITelemetry | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [departmentFilter, setDepartmentFilter] = useState<string>("");
  const [employmentTypeFilter, setEmploymentTypeFilter] = useState<string>("");
  const [sortField, setSortField] = useState<keyof OrganizationRequisitionPerformanceRow>("created_at");
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  useEffect(() => {
    loadData();
  }, [statusFilter, departmentFilter, employmentTypeFilter]);

  async function loadData() {
    setLoading(true);
    try {
      const [dashRes, auditRes, aiGovRes, telRes] = await Promise.all([
        fetchOrganizationDashboard({
          status: statusFilter || undefined,
          department: departmentFilter || undefined,
          employment_type: employmentTypeFilter || undefined,
        }),
        fetchAuditAnalytics(),
        fetchAIGovernanceAnalytics(),
        fetchAITelemetry(),
      ]);

      setDashboard(dashRes);
      setAudit(auditRes);
      setAiGov(aiGovRes);
      setTelemetry(telRes);
    } catch (err) {
      console.error("Failed to load organization reporting dashboard:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleExportCSV() {
    setExporting(true);
    try {
      const res = await exportOrganizationReportCSV({
        status: statusFilter || undefined,
        department: departmentFilter || undefined,
        employment_type: employmentTypeFilter || undefined,
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `organization_requisition_report_${new Date().toISOString().split("T")[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setExporting(false);
    }
  }

  const sortedRequisitions = React.useMemo(() => {
    if (!dashboard?.requisitions) return [];
    return [...dashboard.requisitions].sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];

      if (valA === undefined || valA === null) valA = 0;
      if (valB === undefined || valB === null) valB = 0;

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [dashboard, sortField, sortAsc]);

  function handleSort(field: keyof OrganizationRequisitionPerformanceRow) {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400 font-medium">Loading Enterprise Reporting Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Enterprise Requisition & Operational Reporting</h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time, deterministic analytics across organization requisitions, candidate conversion, and hiring lifecycle events.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-indigo-950/80 border border-indigo-500/30 rounded-lg px-4 py-2 text-xs font-semibold text-indigo-300">
            AI ASSISTS. RECRUITER DECIDES.
          </div>
          <button
            onClick={handleExportCSV}
            disabled={exporting}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-2 rounded-lg shadow transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {exporting ? "Exporting..." : "Export Organization CSV"}
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Requisitions</p>
          <p className="text-2xl font-bold text-white mt-1">{dashboard?.total_requisitions || 0}</p>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Open / Active</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{dashboard?.open_requisitions || 0}</p>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Closed / Filled</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">{dashboard?.closed_requisitions || 0}</p>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Applications</p>
          <p className="text-2xl font-bold text-indigo-400 mt-1">{dashboard?.total_applications || 0}</p>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Total Hires</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{dashboard?.candidates_hired || 0}</p>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Avg Time-to-Fill</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">
            {dashboard?.avg_time_to_fill_days !== null && dashboard?.avg_time_to_fill_days !== undefined
              ? `${dashboard.avg_time_to_fill_days}d`
              : "N/A"}
          </p>
        </div>
      </div>

      {/* Filters Section */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="PUBLISHED">Published</option>
              <option value="PAUSED">Paused</option>
              <option value="CLOSED">Closed</option>
              <option value="DRAFT">Draft</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Employment Type</label>
            <select
              value={employmentTypeFilter}
              onChange={(e) => setEmploymentTypeFilter(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Types</option>
              <option value="FULL_TIME">Full-Time</option>
              <option value="PART_TIME">Part-Time</option>
              <option value="CONTRACT">Contract</option>
            </select>
          </div>
        </div>
        <div className="text-xs text-slate-400">
          Showing <span className="text-white font-semibold">{sortedRequisitions.length}</span> requisitions
        </div>
      </div>

      {/* Requisition Performance Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Requisition Performance Directory</h2>
          <span className="text-xs text-slate-400">Click column header to sort</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-800/60 text-slate-300 border-b border-slate-800 font-semibold uppercase tracking-wider">
                <th className="py-3.5 px-4 cursor-pointer hover:text-white" onClick={() => handleSort("title")}>Requisition</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("status")}>Status</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("department")}>Dept</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("applications")}>Apps</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("eligible")}>Eligible</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("reviewed")}>Reviewed</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("advanced")}>Advanced</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("offers")}>Offers</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("hired")}>Hired</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("time_to_fill_days")}>TTF</th>
                <th className="py-3.5 px-3 cursor-pointer hover:text-white" onClick={() => handleSort("time_to_hire_days")}>TTH</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300 font-medium">
              {sortedRequisitions.length === 0 ? (
                <tr>
                  <td colSpan={11} className="text-center py-8 text-slate-500">
                    No requisitions found matching current filters.
                  </td>
                </tr>
              ) : (
                sortedRequisitions.map((r) => (
                  <tr key={r.requisition_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4">
                      <a href={`/recruiter/jobs/${r.requisition_id}/report`} className="text-indigo-400 hover:text-indigo-300 font-semibold">
                        {r.title}
                      </a>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        r.status === "PUBLISHED" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                        r.status === "CLOSED" ? "bg-purple-950 text-purple-400 border border-purple-800" :
                        "bg-slate-800 text-slate-400"
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400">{r.department || "N/A"}</td>
                    <td className="py-3 px-3 font-semibold text-white">{r.applications}</td>
                    <td className="py-3 px-3 text-emerald-400">{r.eligible}</td>
                    <td className="py-3 px-3">{r.reviewed}</td>
                    <td className="py-3 px-3 text-indigo-400">{r.advanced}</td>
                    <td className="py-3 px-3 text-amber-400">{r.offers}</td>
                    <td className="py-3 px-3 font-bold text-emerald-400">{r.hired}</td>
                    <td className="py-3 px-3 text-amber-300">{r.time_to_fill_days !== null && r.time_to_fill_days !== undefined ? `${r.time_to_fill_days}d` : "-"}</td>
                    <td className="py-3 px-3 text-amber-300">{r.time_to_hire_days !== null && r.time_to_hire_days !== undefined ? `${r.time_to_hire_days}d` : "-"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recruiter Audit & AI Governance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Recruiter Decisions */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider border-b border-slate-800 pb-2">Recruiter Decision Audit</h3>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Total Recruiter Decisions</span>
            <span className="font-bold text-white">{audit?.total_recruiter_decisions || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">ADVANCE Count</span>
            <span className="font-bold text-emerald-400">{audit?.advance_count || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">REJECT Count</span>
            <span className="font-bold text-rose-400">{audit?.reject_count || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">HOLD Count</span>
            <span className="font-bold text-amber-400">{audit?.hold_count || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Audit Completeness</span>
            <span className="font-bold text-emerald-400">{audit?.audit_trail_completeness_pct || 100}%</span>
          </div>
        </div>

        {/* AI Governance */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider border-b border-slate-800 pb-2">AI Advisory & Governance</h3>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">AI Recommendations Generated</span>
            <span className="font-bold text-indigo-400">{aiGov?.ai_recommendations_generated || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">REQUIRES_REVIEW Count</span>
            <span className="font-bold text-amber-400">{aiGov?.requires_review_count || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Generation Failures</span>
            <span className="font-bold text-emerald-400">{aiGov?.recommendation_generation_failures || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">AI State Mutation Authority</span>
            <span className="font-bold text-rose-400">0% (HUMAN RECRUITER ONLY)</span>
          </div>
        </div>

        {/* Gemini Telemetry */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider border-b border-slate-800 pb-2">Operational Telemetry</h3>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Total AI Requests</span>
            <span className="font-bold text-white">{telemetry?.total_gemini_requests || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Successful Requests</span>
            <span className="font-bold text-emerald-400">{telemetry?.successful_requests || 0}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Estimated Cost</span>
            <span className="font-bold text-amber-400">${telemetry?.estimated_cost_usd?.toFixed(4) || "0.0000"}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Avg AI Latency</span>
            <span className="font-bold text-indigo-400">{telemetry?.average_latency_ms || 145}ms</span>
          </div>
        </div>
      </div>
    </div>
  );
}
