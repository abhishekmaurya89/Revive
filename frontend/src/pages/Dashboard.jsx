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

  return (
    <div className="space-y-10">
      <div>
        <div className="text-sm text-muted">Total revenue recovered</div>
        <div className="mt-2 font-display text-6xl text-text">
          {formatMoney(summary?.recovered_amount)}
        </div>
        <div className="mt-2 text-sm text-muted">
          Across failed payments, abandoned checkouts, and overdue
          receivables — every dollar here was at risk before the agent acted.
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Payment recoveries"
          value={payments.successful_recoveries ?? 0}
          sublabel={`${payments.recovery_rate ?? 0}% of ${payments.total_failed_or_abandoned ?? 0} at-risk`}
          accent="text-teal"
        />
        <StatCard
          label="Escalated / pending approval"
          value={payments.escalated_or_pending_approval ?? 0}
          sublabel="Above auto-recovery limit or unclear cause"
          accent="text-amber"
        />
        <StatCard
          label="Stopped by policy"
          value={payments.stopped_by_policy ?? 0}
          sublabel="Hit a stopping rule — no further auto-contact"
          accent="text-red"
        />
        <StatCard
          label="Receivables at risk"
          value={formatMoney(receivables.at_risk_amount)}
          sublabel={`${receivables.open ?? 0} open invoices`}
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
