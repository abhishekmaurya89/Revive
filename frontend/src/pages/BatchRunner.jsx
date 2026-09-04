import { useState } from "react";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import EmptyState from "../components/EmptyState";
import StatCard from "../components/StatCard";
import { formatDateTime, formatMoney } from "../lib/format";

export default function BatchRunner() {
  const { data, refetch } = useApi(() => api.batchHistory(), []);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState(null);
  const [error, setError] = useState(null);

  const batches = data?.batches || [];

  const runBatch = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await api.runBatch();
      setLastRun(result);
      refetch();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="font-display text-3xl text-text">Batch runs</div>
          <div className="mt-1 max-w-xl text-sm text-muted">
            Sweeps every open receivable through the escalation ladder in one
            pass and reports the measured money recovered, escalated, and
            stopped — with a full audit trail for the run.
          </div>
        </div>
        <button
          onClick={runBatch}
          disabled={running}
          className="border border-amber/50 bg-amber/10 px-4 py-2 text-sm text-amber hover:bg-amber/20 disabled:opacity-50"
        >
          {running ? "Running batch…" : "Run batch now"}
        </button>
      </div>

      {error ? (
        <div className="border border-red/30 bg-red/5 px-4 py-3 text-sm text-red">
          {error}
        </div>
      ) : null}

      {lastRun ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <StatCard label="Evaluated" value={lastRun.receivables_evaluated} />
          <StatCard label="Contacted" value={lastRun.receivables_contacted} accent="text-blue" />
          <StatCard label="Escalated" value={lastRun.receivables_escalated} accent="text-amber" />
          <StatCard label="Stopped" value={lastRun.receivables_stopped} accent="text-red" />
          <StatCard
            label="Recovered this run"
            value={formatMoney(lastRun.recovered_amount)}
            accent="text-teal"
          />
        </div>
      ) : null}

      <div className="border border-border bg-surface">
        <div className="border-b border-border px-5 py-3 text-sm text-text">
          Batch history
        </div>
        {batches.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title="No batches run yet"
              description="Click “Run batch now” to sweep open receivables for the first time."
            />
          </div>
        ) : (
          <table className="text-sm">
            <thead>
              <tr className="ledger-row text-left text-xs text-muted">
                <th className="px-5 py-2 font-normal">Batch</th>
                <th className="px-5 py-2 font-normal">Started</th>
                <th className="px-5 py-2 font-normal">Evaluated</th>
                <th className="px-5 py-2 font-normal">Escalated</th>
                <th className="px-5 py-2 font-normal">Stopped</th>
                <th className="px-5 py-2 font-normal">Recovered</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.batch_id} className="ledger-row">
                  <td className="px-5 py-3 font-mono text-xs text-muted">{b.batch_id}</td>
                  <td className="px-5 py-3 font-mono text-xs text-muted">
                    {formatDateTime(b.started_at)}
                  </td>
                  <td className="px-5 py-3 tabular font-mono">{b.receivables_evaluated}</td>
                  <td className="px-5 py-3 tabular font-mono text-amber">
                    {b.receivables_escalated}
                  </td>
                  <td className="px-5 py-3 tabular font-mono text-red">
                    {b.receivables_stopped}
                  </td>
                  <td className="px-5 py-3 tabular font-mono text-teal">
                    {formatMoney(b.recovered_amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
