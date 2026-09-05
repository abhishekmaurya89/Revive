import { useState } from "react";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import AuditTimeline from "../components/AuditTimeline";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import { formatMoney } from "../lib/format";

function outcomeLabel(caseItem) {
  if (caseItem.stopped) return `Stopped: ${(caseItem.policy_code || "policy").replaceAll("_", " ")}`;
  if (caseItem.requires_approval) return "Human approval";
  if (caseItem.recovered_amount) return "Payment recovered";
  if (caseItem.action === "payment_link") return "Razorpay payment link created";
  if (caseItem.action) return `${caseItem.action.replaceAll("_", " ")} requires review`;
  return "No recovery action recorded";
}

export default function BatchRunner() {
  const { data, refetch } = useApi(() => api.batchHistory(), []);
  const [portfolioSize, setPortfolioSize] = useState(42);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState(null);
  const [selectedCase, setSelectedCase] = useState(null);
  const [audit, setAudit] = useState([]);
  const [error, setError] = useState(null);
  const batches = data?.batches || [];
    
  const runBatch = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await api.runBatch(portfolioSize);
      setLastRun(result);
      refetch();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };
    
  const openCase = async (caseItem) => {
    setSelectedCase(caseItem);
    const result = await api.auditFeed(200);
    setAudit((result.audit_trail || []).filter((event) => event.entity_id === caseItem.payment_id));
  };
    
  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="font-display text-3xl text-text">Run the recovery batch.</div>
          <div className="mt-1 max-w-xl text-sm text-muted">
            Review failed Razorpay payments already received through webhooks and inspect their recovery outcomes.
          </div>
        </div>
        <label className="min-w-[220px] text-xs text-muted">
          Accounts in this run <span className="font-mono text-text">{portfolioSize}</span>
          <input type="range" min="20" max="100" value={portfolioSize} onChange={(event) => setPortfolioSize(Number(event.target.value))} className="mt-3 w-full accent-amber" />
          <span className="flex justify-between font-mono text-[10px]"><span>20</span><span>100</span></span>
        </label>
        <button
          onClick={runBatch}
          disabled={running}
          className="border border-amber/50 bg-amber/10 px-4 py-2 text-sm text-amber hover:bg-amber/20 disabled:opacity-50"
        >
          {running ? "Reviewing Razorpay events..." : "Review Razorpay payments"}
        </button>
      </div>
      {error ? (
        <div className="border border-red/30 bg-red/5 px-4 py-3 text-sm text-red">
          {error}
        </div>
      ) : null}
      {lastRun ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
          <StatCard label="₹ at risk" value={formatMoney(lastRun.at_risk_amount)} accent="text-amber" />
          <StatCard label="₹ recovered" value={formatMoney(lastRun.recovered_amount)} accent="text-teal" />
          <StatCard label="Recovery rate" value={`${lastRun.recovery_rate}%`} accent="text-teal" />
          <StatCard label="Prevented loss" value={formatMoney(lastRun.prevented_loss)} accent="text-blue" />
          <StatCard label="Human approval" value={lastRun.requires_approval} accent="text-amber" />
          <StatCard label="Stopped" value={lastRun.stopped} accent="text-red" />
        </div>
      ) : null}
      {lastRun ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <div className="border border-border bg-surface p-3 text-center text-xs text-muted"><span className="font-mono text-lg text-text">{lastRun.accounts_analyzed}</span><br />accounts analyzed</div>
          <div className="border border-border bg-surface p-3 text-center text-xs text-muted"><span className="font-mono text-lg text-text">{lastRun.eligible_for_automation}</span><br />eligible for automation</div>
          <div className="border border-border bg-surface p-3 text-center text-xs text-muted"><span className="font-mono text-lg text-teal">{lastRun.recovered_amount ? formatMoney(lastRun.recovered_amount) : "₹0"}</span><br />recovered from Razorpay</div>
          <div className="border border-border bg-surface p-3 text-center text-xs text-muted"><span className="font-mono text-lg text-red">{lastRun.stopped}</span><br />stopped by policy</div>
        </div>
      ) : null}
      {lastRun?.cases ? (
        <div className="border border-border bg-surface">
          <div className="border-b border-border px-5 py-4"><div className="text-sm text-text">Account decisions</div><div className="mt-1 text-xs text-muted">Select an account to inspect diagnosis, policy, execution, and payment recovery.</div></div>
          <div className="max-h-[520px] overflow-auto"><table className="text-sm"><thead><tr className="ledger-row text-left text-xs text-muted"><th className="px-5 py-2 font-normal">Customer</th><th className="px-5 py-2 font-normal">Signal</th><th className="px-5 py-2 font-normal">At risk</th><th className="px-5 py-2 font-normal">Decision</th><th className="px-5 py-2 font-normal">Outcome</th></tr></thead><tbody>{lastRun.cases.map((caseItem) => <tr key={caseItem.payment_id} onClick={() => openCase(caseItem)} className="ledger-row cursor-pointer hover:bg-raised"><td className="px-5 py-3 font-mono text-xs text-text">{caseItem.customer_id}</td><td className="px-5 py-3 text-xs text-muted">{caseItem.source}</td><td className="px-5 py-3 font-mono tabular">{formatMoney(caseItem.amount)}</td><td className="px-5 py-3"><StatusBadge value={caseItem.action} /></td><td className={`px-5 py-3 text-xs ${caseItem.stopped ? "text-red" : caseItem.requires_approval ? "text-amber" : "text-teal"}`}>{outcomeLabel(caseItem)}</td></tr>)}</tbody></table></div>
        </div>
      ) : null}
      {selectedCase ? (
        <div className="border border-amber/40 bg-surface p-5"><div className="flex flex-wrap items-start justify-between gap-4"><div><div className="text-xs uppercase tracking-[0.16em] text-amber">Case audit</div><div className="mt-1 text-lg text-text">{selectedCase.customer_id} · {formatMoney(selectedCase.amount)}</div><div className="mt-1 text-xs text-muted">{selectedCase.diagnosis.likely_reason} Confidence {Math.round(selectedCase.diagnosis.confidence * 100)}%</div></div><button onClick={() => setSelectedCase(null)} className="text-xs text-muted hover:text-text">Close</button></div><div className="mt-5"><AuditTimeline events={audit} /></div></div>
      ) : null}
      <div className="border border-border bg-surface">
        <div className="border-b border-border px-5 py-3 text-sm text-text">Previous runs</div>
        {batches.length === 0 ? (
          <div className="p-5 text-sm text-muted">Runs will remain available here for comparison.</div>
        ) : (
          <table className="text-sm">
            <tbody>{batches.map((batch) => (
              <tr key={batch.batch_id} className="ledger-row">
                <td className="px-5 py-3 font-mono text-xs text-muted">{batch.batch_id}</td>
                <td className="px-5 py-3">{batch.accounts_analyzed || batch.portfolio_size} analyzed</td>
                <td className="px-5 py-3 text-teal">{formatMoney(batch.recovered_amount)}</td>
                <td className="px-5 py-3 text-red">{batch.stopped ?? batch.receivables_stopped} stopped</td>
              </tr>
            ))}</tbody>
          </table>
        )}
      </div>
    </div>
  );
}
