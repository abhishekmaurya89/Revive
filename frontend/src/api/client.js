const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {}
    throw new Error(detail || `Request to ${path} failed`);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  base: BASE_URL,
  health: () => request("/health"),

  summary: () => request("/recovery/summary"),
  payments: () => request("/recovery/payments"),
  recoveries: () => request("/recovery/recoveries"),

  receivables: (status) =>
    request(`/receivables${status ? `?status=${status}` : ""}`),
  createReceivable: (payload) =>
    request("/receivables", { method: "POST", body: JSON.stringify(payload) }),
  promiseToPay: (invoiceId, payload) =>
    request(`/receivables/${invoiceId}/promise`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  markPaid: (invoiceId, payload) =>
    request(`/receivables/${invoiceId}/mark-paid`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  chaseOne: (invoiceId) => 
    request(`/receivables/${invoiceId}/chase`, { method: "POST" }),
  chaseAll: () => request("/receivables/batch/chase", { method: "POST" }),
  receivableAudit: (invoiceId) => request(`/receivables/${invoiceId}/audit`),

  runBatch: (portfolioSize = 42) => request("/batch/run", {
    method: "POST",
    body: JSON.stringify({ portfolio_size: portfolioSize }),
  }),
  batchHistory: () => request("/batch/history"),
  batchDetail: (batchId) => request(`/batch/${batchId}`),
  batchAudit: (batchId) => request(`/batch/${batchId}/audit`),

  auditFeed: (limit = 200) => request(`/audit?limit=${limit}`),

  simulateCheckoutAbandoned: (payload) =>
    request("/events/checkout-abandoned", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  simulateSubscriptionFailed: (payload) =>
    request("/events/subscription-failed", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
