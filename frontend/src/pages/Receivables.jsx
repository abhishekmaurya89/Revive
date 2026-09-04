import { useState } from "react";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { daysBetween, formatDate, formatMoney } from "../lib/format";

function AddReceivableForm({ onCreated }) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState({
    invoice_id: `INV-${Math.floor(Math.random() * 9000 + 1000)}`,
    customer_id: "cust_demo",
    customer_name: "Demo Customer Pvt Ltd",
    amount: 5000000,
    due_date: new Date().toISOString().slice(0, 10),
  });
  const [error, setError] = useState(null);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="border border-border px-3 py-1.5 text-sm text-muted hover:bg-raised hover:text-text"
      >
        + Add receivable
      </button>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createReceivable({ ...values, amount: Number(values.amount) });
      setOpen(false);
      onCreated();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="grid grid-cols-2 gap-2 border border-border bg-surface p-4 md:grid-cols-5"
    >
      {[
        ["invoice_id", "Invoice ID"],
        ["customer_name", "Customer"],
        ["amount", "Amount (paise)"],
        ["due_date", "Due date"],
      ].map(([name, label]) => (
        <label key={name} className="text-xs text-muted">
          {label}
          <input
            type={name === "due_date" ? "date" : name === "amount" ? "number" : "text"}
            value={values[name]}
            onChange={(e) => setValues((v) => ({ ...v, [name]: e.target.value }))}
            className="mt-1 w-full border border-border bg-raised px-2 py-1.5 text-sm text-text outline-none focus:border-amber"
          />
        </label>
      ))}
      <div className="flex items-end gap-2">
        <button
          type="submit"
          className="border border-amber/50 bg-amber/10 px-3 py-1.5 text-sm text-amber hover:bg-amber/20"
        >
          Create
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="px-3 py-1.5 text-sm text-muted hover:text-text"
        >
          Cancel
        </button>
      </div>
      {error ? <div className="col-span-full text-xs text-red">{error}</div> : null}
    </form>
  );
}

function ReceivableRow({ receivable, onChanged }) {
  const [mode, setMode] = useState(null); // "promise" | "paid" | null
  const [promiseDate, setPromiseDate] = useState(
    new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10)
  );
  const [promiseAmount, setPromiseAmount] = useState(receivable.amount);
  const [paidAmount, setPaidAmount] = useState(receivable.amount);
  const [busy, setBusy] = useState(false);
  const [lastAction, setLastAction] = useState(null);

  const daysOverdue = daysBetween(receivable.due_date);

  const chase = async () => {
    setBusy(true);
    try {
      const result = await api.chaseOne(receivable.invoice_id);
      setLastAction(`${result.action} — ${result.reason}`);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const submitPromise = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.promiseToPay(receivable.invoice_id, {
        promise_to_pay_date: promiseDate,
        amount: Number(promiseAmount),
      });
      setMode(null);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  const submitPaid = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.markPaid(receivable.invoice_id, { recovered_amount: Number(paidAmount) });
      setMode(null);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <tr className="ledger-row align-top">
        <td className="px-5 py-3">
          <div className="text-text">{receivable.customer_name}</div>
          <div className="font-mono text-xs text-muted">{receivable.invoice_id}</div>
        </td>
        <td className="px-5 py-3 tabular font-mono">{formatMoney(receivable.amount)}</td>
        <td className="px-5 py-3 font-mono text-xs text-muted">
          {formatDate(receivable.due_date)}
          <div className={daysOverdue > 0 ? "text-amber" : "text-muted"}>
            {daysOverdue > 0 ? `${daysOverdue}d overdue` : "not yet due"}
          </div>
        </td>
        <td className="px-5 py-3">
          <StatusBadge value={receivable.status} />
        </td>
        <td className="px-5 py-3 text-xs text-muted">
          {receivable.contact_attempts} attempt(s) · level {receivable.escalation_level}
        </td>
        <td className="px-5 py-3">
          <div className="flex flex-wrap gap-2 text-xs">
            <button
              onClick={chase}
              disabled={busy}
              className="border border-border px-2 py-1 text-muted hover:bg-raised hover:text-text disabled:opacity-50"
            >
              Chase now
            </button>
            <button
              onClick={() => setMode(mode === "promise" ? null : "promise")}
              className="border border-border px-2 py-1 text-muted hover:bg-raised hover:text-text"
            >
              Promise to pay
            </button>
            <button
              onClick={() => setMode(mode === "paid" ? null : "paid")}
              className="border border-border px-2 py-1 text-muted hover:bg-raised hover:text-text"
            >
              Mark paid
            </button>
          </div>
          {lastAction ? (
            <div className="mt-2 text-xs text-teal">{lastAction}</div>
          ) : null}
        </td>
      </tr>

      {mode === "promise" ? (
        <tr className="ledger-row bg-raised/40">
          <td colSpan={6} className="px-5 py-3">
            <form onSubmit={submitPromise} className="flex flex-wrap items-end gap-3 text-xs">
              <label className="text-muted">
                Promise date
                <input
                  type="date"
                  value={promiseDate}
                  onChange={(e) => setPromiseDate(e.target.value)}
                  className="mt-1 block border border-border bg-raised px-2 py-1 text-text"
                />
              </label>
              <label className="text-muted">
                Amount (paise)
                <input
                  type="number"
                  value={promiseAmount}
                  onChange={(e) => setPromiseAmount(e.target.value)}
                  className="mt-1 block border border-border bg-raised px-2 py-1 text-text"
                />
              </label>
              <button className="border border-blue/50 bg-blue/10 px-3 py-1.5 text-blue hover:bg-blue/20">
                Save promise
              </button>
            </form>
          </td>
        </tr>
      ) : null}

      {mode === "paid" ? (
        <tr className="ledger-row bg-raised/40">
          <td colSpan={6} className="px-5 py-3">
            <form onSubmit={submitPaid} className="flex flex-wrap items-end gap-3 text-xs">
              <label className="text-muted">
                Recovered amount (paise)
                <input
                  type="number"
                  value={paidAmount}
                  onChange={(e) => setPaidAmount(e.target.value)}
                  className="mt-1 block border border-border bg-raised px-2 py-1 text-text"
                />
              </label>
              <button className="border border-teal/50 bg-teal/10 px-3 py-1.5 text-teal hover:bg-teal/20">
                Record payment
              </button>
            </form>
          </td>
        </tr>
      ) : null}
    </>
  );
}

function ChaseAllButton({ onDone }) {
  const [chasing, setChasing] = useState(false);

  const run = async () => {
    setChasing(true);
    try {
      const result = await api.chaseAll();
      onDone(result);
    } finally {
      setChasing(false);
    }
  };

  return (
    <button
      onClick={run}
      disabled={chasing}
      className="border border-amber/50 bg-amber/10 px-3 py-1.5 text-sm text-amber hover:bg-amber/20 disabled:opacity-50"
    >
      {chasing ? "Chasing…" : "Chase all open"}
    </button>
  );
}

export default function Receivables() {
  const { data, refetch } = useApi(() => api.receivables(), []);
  const [chaseResult, setChaseResult] = useState(null);
  const receivables = data?.receivables || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="font-display text-3xl text-text">B2B receivables</div>
          <div className="mt-1 text-sm text-muted">
            A compliant escalation ladder — reminder, chase email, voice
            call, then a human owner — with cooldowns and a contact cap so
            the agent never over-reaches.
          </div>
        </div>
        <div className="flex gap-3">
          <ChaseAllButton
            onDone={(result) => {
              setChaseResult(result);
              refetch();
            }}
          />
          <AddReceivableForm onCreated={refetch} />
        </div>
      </div>

      {chaseResult ? (
        <div className="border border-teal/30 bg-teal/5 px-4 py-3 text-sm text-teal">
          Evaluated {chaseResult.evaluated} · contacted {chaseResult.contacted} ·
          escalated {chaseResult.escalated} · stopped {chaseResult.stopped}
        </div>
      ) : null}

      <div className="border border-border bg-surface">
        {receivables.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="No receivables yet"
            />
          </div>
        ) : (
          <table className="text-sm">
            <thead>
              <tr className="ledger-row text-left text-xs text-muted">
                <th className="px-5 py-2 font-normal">Customer</th>
                <th className="px-5 py-2 font-normal">Amount</th>
                <th className="px-5 py-2 font-normal">Due</th>
                <th className="px-5 py-2 font-normal">Status</th>
                <th className="px-5 py-2 font-normal">Outreach</th>
                <th className="px-5 py-2 font-normal">Actions</th>
              </tr>
            </thead>
            <tbody>
              {receivables.map((r) => (
                <ReceivableRow key={r.invoice_id} receivable={r} onChanged={refetch} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
