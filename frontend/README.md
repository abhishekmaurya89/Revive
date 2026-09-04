# Revive Console

A Vite + React + Tailwind dashboard for the Revive revenue-recovery backend.

## Pages

- **Overview** — total revenue recovered, breakdown by source, recent audit activity.
- **Payments & checkout** — recovery decisions the agent has made for failed payments, and simulators to send checkout-abandonment / subscription-failure signals without needing a real Razorpay webhook.
- **Receivables** — the B2B receivables chaser: escalation status, promise-to-pay tracking, one-off or batch chasing.
- **Batch runs** — trigger a sweep of every open receivable and see measured money recovered, escalations, and stopping-rule hits, plus run history.
- **Audit trail** — every diagnosis, decision, policy check, execution, and stopping rule, filterable by entity type.
