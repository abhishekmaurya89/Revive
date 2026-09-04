import { useState } from "react";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { formatDateTime, formatMoney } from "../lib/format";

function SimulatorForm({ title, description, fields, onSubmit }) {
  const [values, setValues] = useState(
    Object.fromEntries(fields.map((f) => [f.name, f.default ?? ""]))
  );
  const [status, setStatus] = useState(null);

  const handleChange = (name) => (e) =>
    setValues((v) => ({ ...v, [name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("loading");
    try {
      const payload = Object.fromEntries(
        fields.map((f) => [
          f.name,
          f.type === "number" ? Number(values[f.name]) : values[f.name],
        ])
      );
      const result = await onSubmit(payload);
      setStatus({
        ok: true,
        message:
          result?.recovery?.action
            ? `Agent chose "${result.recovery.action}" — ${result.recovery.reason || ""}`
            : "Signal processed.",
      });
    } catch (err) {
      setStatus({ ok: false, message: err.message });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border border-border bg-surface p-5">
      <div className="text-sm text-text">{title}</div>
      <div className="mt-1 text-xs text-muted">{description}</div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        {fields.map((field) => (
          <label key={field.name} className="text-xs text-muted">
            {field.label}
            <input
              type={field.type || "text"}
              value={values[field.name]}
              onChange={handleChange(field.name)}
              required
              className="mt-1 w-full border border-border bg-raised px-2 py-1.5 text-sm text-text outline-none focus:border-amber"
            />
          </label>
        ))}
      </div>

      <button
        type="submit"
        disabled={status === "loading"}
        className="mt-4 border border-amber/50 bg-amber/10 px-3 py-1.5 text-sm text-amber hover:bg-amber/20 disabled:opacity-50"
      >
        {status === "loading" ? "Sending…" : "Send signal"}
      </button>

      {status && status !== "loading" ? (
        <div className={`mt-3 text-xs ${status.ok ? "text-teal" : "text-red"}`}>
          {status.message}
        </div>
      ) : null}
    </form>
  );
}

export default function Payments() {
  const { data: paymentsData, refetch: refetchPayments } = useApi(
    () => api.payments(),
    []
  );
  const { data: recoveriesData, refetch: refetchRecoveries } = useApi(
    () => api.recoveries(),
    []
  );

  const recoveries = recoveriesData?.recoveries || [];

  const refetchAll = () => {
    refetchPayments();
    refetchRecoveries();
  };

  return (
    <div className="space-y-8">
      <div>
        <div className="font-display text-3xl text-text">Payments &amp; checkout</div>
        <div className="mt-1 text-sm text-muted">
          Every payment failure, checkout abandonment, and subscription
          retry the agent has diagnosed and acted on.
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <SimulatorForm
          title="Simulate a checkout abandonment"
          description="Sends a drop-off signal through the same detect → diagnose → recover loop as a real webhook."
          fields={[
            { name: "order_id", label: "Order ID", default: `order_${Date.now().toString(36)}` },
            { name: "customer_id", label: "Customer ID", default: "cust_demo" },
            { name: "amount", label: "Amount (paise)", type: "number", default: 250000 },
            { name: "currency", label: "Currency", default: "INR" },
          ]}
          onSubmit={async (payload) => {
            const result = await api.simulateCheckoutAbandoned(payload);
            refetchAll();
            return result;
          }}
        />

        <SimulatorForm
          title="Simulate a subscription failure"
          description="Mirrors a mandate/recurring charge failure from a billing system."
          fields={[
            { name: "subscription_id", label: "Subscription ID", default: `sub_${Date.now().toString(36)}` },
            { name: "customer_id", label: "Customer ID", default: "cust_demo" },
            { name: "amount", label: "Amount (paise)", type: "number", default: 99900 },
            { name: "attempt_count", label: "Attempt #", type: "number", default: 1 },
          ]}
          onSubmit={async (payload) => {
            const result = await api.simulateSubscriptionFailed(payload);
            refetchAll();
            return result;
          }}
        />
      </div>

      <div className="border border-border bg-surface">
        <div className="border-b border-border px-5 py-3 text-sm text-text">
          Recovery decisions
        </div>
        {recoveries.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="No recovery decisions yet"
              description="Send a webhook or use a simulator above to see the agent act."
            />
          </div>
        ) : (
          <table className="text-sm">
            <thead>
              <tr className="ledger-row text-left text-xs text-muted">
                <th className="px-5 py-2 font-normal">Payment</th>
                <th className="px-5 py-2 font-normal">Amount</th>
                <th className="px-5 py-2 font-normal">Action</th>
                <th className="px-5 py-2 font-normal">Status</th>
                <th className="px-5 py-2 font-normal">Policy outcome</th>
                <th className="px-5 py-2 font-normal">When</th>
              </tr>
            </thead>
            <tbody>
              {recoveries.map((r) => (
                <tr key={r.recovery_id} className="ledger-row">
                  <td className="px-5 py-3 font-mono text-xs text-muted">
                    {r.payment_id}
                  </td>
                  <td className="px-5 py-3 tabular font-mono">
                    {formatMoney(r.amount || 0)}
                  </td>
                  <td className="px-5 py-3">
                    <StatusBadge value={r.action} />
                  </td>
                  <td className="px-5 py-3">
                    <StatusBadge value={r.status} />
                  </td>
                  <td className="px-5 py-3 text-xs text-muted">
                    {r.stopped
                      ? "Stopped by policy"
                      : r.requires_approval
                      ? "Needs approval"
                      : r.policy_allowed
                      ? "Executed"
                      : r.policy_reason}
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-muted">
                    {formatDateTime(r.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
