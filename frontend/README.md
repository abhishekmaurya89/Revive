# Revive Console

The React dashboard for the Revive revenue-recovery backend.


## Real workflows

- **Payments & checkout** shows payment failures and recoveries received from Razorpay. It does not generate demo payments.
- **Checkout abandonment** is reported by the merchant checkout to `POST /events/checkout-abandoned` with the `X-Checkout-Event-Key` header. Configure `CHECKOUT_EVENT_SECRET` in the backend.
- **Receivables** are invoice records entered by an operator. Overdue chasing creates a Razorpay Payment Link and can send Razorpay email/SMS notifications when customer contact details are present.
- **Batch runs** review real failed or abandoned payment records already stored from Razorpay events. They do not create synthetic accounts.
- **Audit trail** records diagnoses, policy decisions, Razorpay actions, webhook confirmations, escalations, and stopping rules.

Amounts are entered in paise. For example, `250000` represents INR 2,500.
