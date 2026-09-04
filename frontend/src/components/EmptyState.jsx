export default function EmptyState({ title, description }) {
  return (
    <div className="border border-dashed border-border p-8 text-center">
      <div className="text-text">{title}</div>
      {description ? (
        <div className="mt-1 text-sm text-muted">{description}</div>
      ) : null}
    </div>
  );
}
