import { formatDateTime } from "../lib/format";
import EmptyState from "./EmptyState";

const EVENT_LABELS = {
  event_received: "Signal received",
  diagnosis: "Diagnosed",
  decision: "Action chosen",
  policy_check: "Policy checked",
  execution: "Action executed",
  created: "Receivable created",
  chase_evaluated: "Chase evaluated",
  promise_to_pay_recorded: "Promise to pay recorded",
  payment_recorded: "Payment recorded",
  batch_completed: "Batch completed",
};

export default function AuditTimeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <EmptyState
        title="No audit events yet"
        description="Actions taken by the agent will appear here as soon as it runs."
      />
    );
  }

  return (
    <ol className="space-y-0">
      {events.map((event, index) => (
        <li
          key={event.audit_id || index}
          className="border-l border-border pl-4 pb-5 last:pb-0 relative"
        >
          <span className="absolute -left-[5px] top-1 h-2 w-2 rounded-full bg-amber" />
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <span className="text-sm text-text">
              {EVENT_LABELS[event.event_type] || event.event_type}
            </span>
            <span className="font-mono text-xs text-muted tabular">
              {formatDateTime(event.timestamp)}
            </span>
          </div>
          <div className="text-xs text-muted">
            {event.entity_type} · {event.entity_id}
          </div>
          {event.details && Object.keys(event.details).length > 0 ? (
            <pre className="mt-2 overflow-x-auto rounded-sm bg-raised p-2 font-mono text-xs text-muted">
              {JSON.stringify(event.details, null, 2)}
            </pre>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
