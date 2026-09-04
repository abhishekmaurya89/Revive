import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import StatCard from "../components/StatCard";
import BarList from "../components/BarList";
import AuditTimeline from "../components/AuditTimeline";
import EmptyState from "../components/EmptyState";
import { formatMoney } from "../lib/format";

export default function Dashboard() {
  const { data: summary, error: summaryError, loading: summaryLoading } = useApi(
    () => api.summary(),
    []
  );
  const { data: auditData } = useApi(() => api.auditFeed(8), []);
  const { data: batchData } = useApi(() => api.batchHistory(), []);

  if (summaryLoading) {
    return <div className="text-muted">Loading recovery summary…</div>;
  }

  if (summaryError) {
    return (
      <EmptyState
        title="Can't reach the Revive API"
        description={`${summaryError} — confirm the backend is running at the configured VITE_API_BASE_URL.`}
      />
    );
  }

  const payments = summary?.payments || {};
  const receivables = summary?.receivables || {};
  const latestBatch = batchData?.batches?.[0];

  return (
    <div className="space-y-10">
      <div className="border border-border bg-surface p-6 lg:p-8">
        <div className="text-xs uppercase tracking-[0.18em] text-amber">Revive recovery command center</div>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-6">
          <div><div className="text-sm text-muted">Revenue at risk</div><div className="mt-1 font-display text-5xl text-text">{formatMoney(latestBatch?.at_risk_amount || receivables.at_risk_amount)}</div><div className="mt-2 max-w-xl text-sm text-muted">Revive diagnoses each failure, applies policy, and recovers eligible payments while visibly stopping unsafe actions.</div></div>
          <Link to="/batches" className="bg-amber px-4 py-2.5 text-sm font-medium text-ink hover:bg-[#ffc15b]">Run recovery batch</Link>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="₹ recovered"
          value={formatMoney(latestBatch?.recovered_amount || summary?.recovered_amount)}
          sublabel={`${latestBatch?.recovery_rate ?? payments.recovery_rate ?? 0}% recovery rate`}
          accent="text-teal"
        />
        <StatCard
          label="Escalated / pending approval"
          value={latestBatch?.requires_approval ?? payments.escalated_or_pending_approval ?? 0}
          sublabel="Human approval required"
          accent="text-amber"
        />
        <StatCard
          label="Stopped by policy"
          value={latestBatch?.stopped ?? payments.stopped_by_policy ?? 0}
          sublabel="Hit a stopping rule — no further auto-contact"
          accent="text-red"
        />
        <StatCard
          label="Receivables at risk"
          value={latestBatch?.accounts_analyzed ?? receivables.open ?? 0}
          sublabel="accounts analyzed in latest batch"
          accent="text-blue"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="border border-border bg-surface p-6">
          <div className="text-sm text-text">Recovered amount by source</div>
          <div className="mt-5">
            <BarList
              items={[
                {
                  label: "Payments & checkout",
                  value: payments.recovered_amount || 0,
                  display: formatMoney(payments.recovered_amount),
                  color: "bg-teal",
                },
                {
                  label: "B2B receivables",
                  value: receivables.recovered_amount || 0,
                  display: formatMoney(receivables.recovered_amount),
                  color: "bg-blue",
                },
              ]}
            />
          </div>
          <div className="mt-6 flex gap-3 text-sm">
            <Link
              to="/batches"
              className="border border-border px-3 py-1.5 text-text hover:bg-raised"
            >
              Run a batch
            </Link>
            <Link
              to="/receivables"
              className="border border-border px-3 py-1.5 text-muted hover:bg-raised hover:text-text"
            >
              View receivables
            </Link>
          </div>
        </div>

        <div className="border border-border bg-surface p-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-text">Recent activity</div>
            <Link to="/audit" className="text-xs text-muted hover:text-text">
              View full trail
            </Link>
          </div>
          <div className="mt-5">
            <AuditTimeline events={auditData?.audit_trail} />
          </div>
        </div>
      </div>
    </div>
  );
}
