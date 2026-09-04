import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/payments", label: "Payments & checkout" },
  { to: "/receivables", label: "Receivables" },
  { to: "/batches", label: "Batch runs" },
  { to: "/audit", label: "Audit trail" },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-ink">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border px-5 py-6">
        <div>
          <div className="font-display text-2xl text-text">Revive</div>
          <div className="mt-1 text-sm text-muted">
            Revenue recovery console
          </div>
        </div>

        <nav className="mt-10 flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-sm px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-raised text-text"
                    : "text-muted hover:bg-raised/60 hover:text-text"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto pt-8 text-xs text-muted">
          Every automated action is logged to the audit trail and bounded by the
          policy layer's stopping rules.
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto px-10 py-8">
        <Outlet />
      </main>
    </div>
  );
}
