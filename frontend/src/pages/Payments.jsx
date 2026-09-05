import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { formatDateTime, formatMoney } from "../lib/format";

export default function Payments() {
  const { data: recoveriesData } = useApi(
    () => api.recoveries(),
    []
  );

  const recoveries = recoveriesData?.recoveries || [];

  return (
    <div className="space-y-8">
      <div>
        <div className="font-display text-3xl text-text">Payments &amp; checkout</div>
        <div className="mt-1 text-sm text-muted">
          Every Razorpay payment failure the agent has diagnosed and acted on.
        </div>
      </div>

      <div className="border border-border bg-surface">
        <div className="border-b border-border px-5 py-3 text-sm text-text">
          Recovery decisions
        </div>
        {recoveries.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="No recovery decisions yet"
              description="Send a signed Razorpay webhook to see the agent act."
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
