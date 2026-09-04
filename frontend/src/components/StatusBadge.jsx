const STYLES = {
  // payment statuses
  success: "text-teal border-teal/40 bg-teal/10",
  failed: "text-red border-red/40 bg-red/10",
  abandoned: "text-amber border-amber/40 bg-amber/10",

  // recovery statuses
  recovered: "text-teal border-teal/40 bg-teal/10",
  payment_link_created: "text-blue border-blue/40 bg-blue/10",
  created: "text-blue border-blue/40 bg-blue/10",

  // receivable statuses
  open: "text-muted border-border bg-raised",
  overdue: "text-amber border-amber/40 bg-amber/10",
  promised: "text-blue border-blue/40 bg-blue/10",
  partially_paid: "text-blue border-blue/40 bg-blue/10",
  escalated: "text-red border-red/40 bg-red/10",
  do_not_contact: "text-muted border-border bg-raised",
  write_off_review: "text-red border-red/40 bg-red/10",

  // generic
  true: "text-teal border-teal/40 bg-teal/10",
  false: "text-muted border-border bg-raised",
};

export default function StatusBadge({ value }) {
  const key = String(value ?? "").toLowerCase();
  const style = STYLES[key] || "text-muted border-border bg-raised";
  const label = key ? key.replaceAll("_", " ") : "unknown";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-mono lowercase ${style}`}
    >
      {label}
    </span>
  );
}
