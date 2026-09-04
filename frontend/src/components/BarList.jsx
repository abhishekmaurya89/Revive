export default function BarList({ items }) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex items-baseline justify-between text-sm">
            <span className="text-text">{item.label}</span>
            <span className="font-mono text-muted tabular">{item.display}</span>
          </div>
          <div className="h-1.5 w-full bg-raised">
            <div
              className={`h-1.5 ${item.color || "bg-amber"}`}
              style={{ width: `${Math.max((item.value / max) * 100, 2)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
