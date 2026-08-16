"use client";

import React, { useEffect, useState } from "react";
import {
  WebhookSubscription,
  WebhookEventResponse,
  fetchWebhookSubscriptions,
  createWebhookSubscription,
  updateWebhookSubscription,
  deleteWebhookSubscription,
  rotateWebhookSecret,
  sendTestWebhook,
  fetchWebhookDeliveryHistory,
} from "@/lib/api";

const ALL_EVENTS = [
  { id: "job.intelligence.completed", label: "Job Intelligence Completed" },
  { id: "offer.created", label: "Offer Created" },
  { id: "offer.accepted", label: "Offer Accepted" },
  { id: "candidate.hired", label: "Candidate Hired" },
];

export default function WebhookSettingsPage() {
  const [subscriptions, setSubscriptions] = useState<WebhookSubscription[]>([]);
  const [history, setHistory] = useState<WebhookEventResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals & Forms
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [endpointUrl, setEndpointUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([
    "offer.accepted",
    "candidate.hired",
  ]);

  // One-time secret display state
  const [newSecretModal, setNewSecretModal] = useState<string | null>(null);

  // Testing state
  const [testingSubId, setTestingSubId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; success: boolean; status?: number } | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [subs, evts] = await Promise.all([
        fetchWebhookSubscriptions(),
        fetchWebhookDeliveryHistory(),
      ]);
      setSubscriptions(subs);
      setHistory(evts);
    } catch (err: any) {
      setError(err.message || "Failed to load webhook settings");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!endpointUrl) return;
    try {
      const created = await createWebhookSubscription({
        endpoint_url: endpointUrl,
        subscribed_events: selectedEvents,
      });
      if (created) {
        setNewSecretModal(created.secret);
        setIsCreateOpen(false);
        setEndpointUrl("");
        loadData();
      }
    } catch (err: any) {
      alert(`Error creating webhook: ${err.message}`);
    }
  }

  async function handleToggleEnabled(sub: WebhookSubscription) {
    try {
      await updateWebhookSubscription(sub.id, { enabled: !sub.enabled });
      loadData();
    } catch (err: any) {
      alert(`Error updating webhook: ${err.message}`);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Are you sure you want to delete this webhook subscription?")) return;
    try {
      await deleteWebhookSubscription(id);
      loadData();
    } catch (err: any) {
      alert(`Error deleting webhook: ${err.message}`);
    }
  }

  async function handleRotateSecret(id: string) {
    if (!confirm("Are you sure you want to rotate the signing secret? Existing integrations must be updated.")) return;
    try {
      const res = await rotateWebhookSecret(id);
      if (res) {
        setNewSecretModal(res.new_secret);
      }
    } catch (err: any) {
      alert(`Error rotating secret: ${err.message}`);
    }
  }

  async function handleSendTest(id: string) {
    setTestingSubId(id);
    setTestResult(null);
    try {
      const res = await sendTestWebhook(id);
      if (res) {
        setTestResult({
          id,
          success: res.delivered,
          status: res.http_status,
        });
      }
    } catch (err: any) {
      setTestResult({ id, success: false });
    } finally {
      setTestingSubId(null);
      loadData();
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Outbound Enterprise Webhooks</h1>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 border border-emerald-300">
              HMAC-SHA256 Signed
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Configure tenant-isolated webhook notifications for external ATS and HRIS integration boundaries.
          </p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors"
        >
          + Add Webhook Endpoint
        </button>
      </div>

      {/* Secret Display Modal (Shown ONCE) */}
      {newSecretModal && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-sm font-bold text-amber-800">Signing Secret Generated (Exposed ONCE)</h3>
              <p className="text-xs text-amber-700 mt-1">
                Copy and store this secret securely. It will not be shown again in API responses or UI.
              </p>
              <div className="mt-2 font-mono bg-white p-2 text-xs border border-amber-300 rounded text-slate-800 select-all">
                {newSecretModal}
              </div>
            </div>
            <button
              onClick={() => setNewSecretModal(null)}
              className="text-amber-600 hover:text-amber-800 text-xs font-bold"
            >
              Dismiss ✕
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-500 text-sm">Loading webhook configuration...</div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">{error}</div>
      ) : (
        <div className="space-y-8">
          {/* Subscriptions Table */}
          <div className="bg-white shadow border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                Active Webhook Subscriptions ({subscriptions.length})
              </h2>
            </div>
            {subscriptions.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-sm">
                No webhook subscriptions configured. Click &quot;+ Add Webhook Endpoint&quot; to create one.
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {subscriptions.map((sub) => (
                  <div key={sub.id} className="p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm font-semibold text-gray-900">{sub.endpoint_url}</span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            sub.enabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {sub.enabled ? "ACTIVE" : "DISABLED"}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {sub.subscribed_events.map((evt) => (
                          <span
                            key={evt}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
                          >
                            {evt}
                          </span>
                        ))}
                      </div>
                      <p className="text-xs text-gray-400">Created: {new Date(sub.created_at).toLocaleString()}</p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleSendTest(sub.id)}
                        disabled={testingSubId === sub.id}
                        className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
                      >
                        {testingSubId === sub.id ? "Testing..." : "Send Test"}
                      </button>
                      <button
                        onClick={() => handleRotateSecret(sub.id)}
                        className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded border border-amber-200 transition-colors"
                      >
                        Rotate Secret
                      </button>
                      <button
                        onClick={() => handleToggleEnabled(sub)}
                        className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded border border-gray-200 transition-colors"
                      >
                        {sub.enabled ? "Disable" : "Enable"}
                      </button>
                      <button
                        onClick={() => handleDelete(sub.id)}
                        className="px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded border border-red-200 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Delivery Audit History */}
          <div className="bg-white shadow border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                Outbound Delivery Audit History ({history.length})
              </h2>
            </div>
            {history.length === 0 ? (
              <div className="p-6 text-center text-gray-500 text-sm">No delivery attempts logged yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-left text-xs text-gray-700">
                  <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider">
                    <tr>
                      <th className="px-6 py-3">Event Type</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Attempts</th>
                      <th className="px-6 py-3">HTTP Code</th>
                      <th className="px-6 py-3">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {history.map((h) => (
                      <tr key={h.id}>
                        <td className="px-6 py-4 font-mono text-gray-900 font-medium">{h.event_type}</td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-2 py-0.5 rounded-full font-semibold ${
                              h.delivery_status === "DELIVERED"
                                ? "bg-emerald-100 text-emerald-800"
                                : h.delivery_status === "RETRYING"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-rose-100 text-rose-800"
                            }`}
                          >
                            {h.delivery_status}
                          </span>
                        </td>
                        <td className="px-6 py-4">{h.attempt_count}</td>
                        <td className="px-6 py-4 font-mono">{h.last_http_status || "-"}</td>
                        <td className="px-6 py-4 text-gray-500">{new Date(h.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900">Add Webhook Endpoint</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Destination HTTPS URL
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://api.yourcompany.com/webhooks"
                  value={endpointUrl}
                  onChange={(e) => setEndpointUrl(e.target.value)}
                  className="w-full text-sm p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-2">
                  Subscribed Event Types
                </label>
                <div className="space-y-2">
                  {ALL_EVENTS.map((evt) => (
                    <label key={evt.id} className="flex items-center gap-2 text-xs text-gray-700">
                      <input
                        type="checkbox"
                        checked={selectedEvents.includes(evt.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEvents([...selectedEvents, evt.id]);
                          } else {
                            setSelectedEvents(selectedEvents.filter((x) => x !== evt.id));
                          }
                        }}
                        className="rounded text-indigo-600 focus:ring-indigo-500"
                      />
                      <span>{evt.label} ({evt.id})</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm"
                >
                  Create Subscription
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
