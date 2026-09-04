export default function StatCard({
  label,
  value,
  sublabel,
  accent = "text-text",
}) {
  return (
    <div className="border border-border bg-surface p-5">
      <div className="text-sm text-muted">{label}</div>
      <div className={`mt-2 font-mono text-2xl tabular ${accent}`}>{value}</div>
      {sublabel ? (
        <div className="mt-1 text-xs text-muted">{sublabel}</div>
      ) : null}
    </div>
  );
}
