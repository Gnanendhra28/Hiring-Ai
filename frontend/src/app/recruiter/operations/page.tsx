"use client";

import React, { useEffect, useState } from "react";
import { OperationsMetricsResponse, fetchOperationsMetrics } from "@/lib/api";

export default function OperationsDashboardPage() {
  const [metrics, setMetrics] = useState<OperationsMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  async function loadMetrics() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOperationsMetrics();
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || "Failed to load operational metrics");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">System Operations & Metric Observability</h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
              HEALTHY
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Real-time platform throughput, tenant API rate-limit quotas, webhook delivery metrics, and AI service health.
          </p>
        </div>
        <button
          onClick={loadMetrics}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg shadow-sm transition-colors"
        >
          ↻ Refresh Observability Metrics
        </button>
      </div>

      {/* AI Governance Advisory Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-5 rounded-xl shadow border border-indigo-800/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">Governance Policy</span>
          </div>
          <p className="text-base font-bold tracking-tight text-white">AI ASSISTS. RECRUITER DECIDES.</p>
          <p className="text-xs text-slate-300">
            Rate limiting and metrics telemetry have 0% state mutation authority over candidate application stages or hiring decisions.
          </p>
        </div>
        <div className="text-right flex flex-col items-end">
          <span className="text-xs text-slate-400">AI Mutation Paths</span>
          <span className="text-xl font-extrabold text-emerald-400">0</span>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500 text-sm">Loading operational metrics...</div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">{error}</div>
      ) : metrics ? (
        <div className="space-y-8">
          {/* System Health Cards */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">
              Infrastructure & Service Health
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-gray-500">API Backend Status</span>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold text-emerald-700">{metrics.system_health.backend_status}</span>
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-gray-500">Worker Status</span>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold text-emerald-700">{metrics.system_health.worker_status}</span>
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-gray-500">AI Service (Gemini)</span>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold text-emerald-700">{metrics.system_health.ai_service_status}</span>
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between">
                <span className="text-xs font-medium text-gray-500">Container Restarts</span>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-lg font-bold text-gray-900">{metrics.system_health.container_restarts}</span>
                  <span className="text-xs text-gray-400">0 Restarts</span>
                </div>
              </div>
            </div>
          </div>

          {/* Rate Limiting Quota Tiers */}
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">
              Tenant Rate Limiting & Quotas
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                <span className="text-xs font-medium text-gray-500">Read API Quota</span>
                <p className="text-base font-bold text-indigo-700 mt-1">{metrics.rate_limiting.read_api_limit}</p>
                <p className="text-xs text-gray-400 mt-1">Jobs, Requisitions, Reports</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                <span className="text-xs font-medium text-gray-500">State Change Quota</span>
                <p className="text-base font-bold text-indigo-700 mt-1">{metrics.rate_limiting.state_change_limit}</p>
                <p className="text-xs text-gray-400 mt-1">Decisions, Offers, Hires</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                <span className="text-xs font-medium text-gray-500">AI Processing Quota</span>
                <p className="text-base font-bold text-indigo-700 mt-1">{metrics.rate_limiting.ai_api_limit}</p>
                <p className="text-xs text-gray-400 mt-1">Intelligence & Resumes</p>
              </div>

              <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                <span className="text-xs font-medium text-gray-500">Webhook Management Quota</span>
                <p className="text-base font-bold text-indigo-700 mt-1">{metrics.rate_limiting.webhook_api_limit}</p>
                <p className="text-xs text-gray-400 mt-1">Subscriptions & Tests</p>
              </div>
            </div>
          </div>

          {/* Webhook & AI Observability Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Webhook Observability */}
            <div className="bg-white shadow border border-gray-200 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                <h3 className="text-sm font-bold text-gray-900">Webhook Outbound Observability</h3>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                  {metrics.webhook_observability.success_rate_percent}% Success
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="block text-xs text-gray-500">Total Events</span>
                  <span className="text-lg font-bold text-gray-900">{metrics.webhook_observability.total_events}</span>
                </div>
                <div className="bg-emerald-50 p-3 rounded-lg">
                  <span className="block text-xs text-emerald-700">Delivered</span>
                  <span className="text-lg font-bold text-emerald-800">{metrics.webhook_observability.delivered}</span>
                </div>
                <div className="bg-amber-50 p-3 rounded-lg">
                  <span className="block text-xs text-amber-700">Retrying</span>
                  <span className="text-lg font-bold text-amber-800">{metrics.webhook_observability.retrying}</span>
                </div>
                <div className="bg-rose-50 p-3 rounded-lg">
                  <span className="block text-xs text-rose-700">Failed</span>
                  <span className="text-lg font-bold text-rose-800">{metrics.webhook_observability.failed}</span>
                </div>
              </div>
            </div>

            {/* AI Telemetry & Cost Attribution */}
            <div className="bg-white shadow border border-gray-200 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                <h3 className="text-sm font-bold text-gray-900">AI Operational Telemetry</h3>
                <span className="text-xs text-gray-500 font-mono">Gemini 1.5 Flash</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-center">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="block text-xs text-gray-500">Total Requests</span>
                  <span className="text-lg font-bold text-gray-900">{metrics.ai_observability?.total_requests || 0}</span>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="block text-xs text-gray-500">Tokens Processed</span>
                  <span className="text-lg font-bold text-gray-900">{metrics.ai_observability?.total_token_estimate || 0}</span>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="block text-xs text-gray-500">Est. Cost (USD)</span>
                  <span className="text-lg font-bold text-emerald-700">
                    ${(metrics.ai_observability?.total_estimated_cost_usd || 0).toFixed(5)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
