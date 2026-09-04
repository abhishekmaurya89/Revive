import { useMemo, useState } from "react";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import AuditTimeline from "../components/AuditTimeline";

const FILTERS = [
  { value: "all", label: "All" },
  { value: "payment", label: "Payments" },
  { value: "receivable", label: "Receivables" },
  { value: "batch", label: "Batches" },
];

export default function AuditTrail() {
  const { data, loading, error } = useApi(() => api.auditFeed(300), []);
  const [filter, setFilter] = useState("all");

  const events = data?.audit_trail || [];
  const filtered = useMemo(
    () => (filter === "all" ? events : events.filter((e) => e.entity_type === filter)),
    [events, filter]
  );

  return (
    <div className="space-y-6">
      <div>
        <div className="font-display text-3xl text-text">Audit trail</div>
        <div className="mt-1 text-sm text-muted">
          Every diagnosis, decision, policy check, execution, and stopping
          rule the agent has triggered, in order.
        </div>
      </div>

      <div className="flex gap-2 text-sm">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`border px-3 py-1.5 ${
              filter === f.value
                ? "border-amber/50 bg-amber/10 text-amber"
                : "border-border text-muted hover:bg-raised hover:text-text"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="border border-border bg-surface p-6">
        {loading ? (
          <div className="text-muted">Loading audit trail…</div>
        ) : error ? (
          <div className="text-red">{error}</div>
        ) : (
          <AuditTimeline events={filtered} />
        )}
      </div>
    </div>
  );
}
