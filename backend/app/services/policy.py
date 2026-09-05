from dataclasses import dataclass

from app.agents.schemas import RecoveryAction, RecoveryDecision
from app.config import settings
from app.models.payment import PaymentEvent, PaymentStatus
from app.models.receivable import ChaseAction, Receivable, ReceivableStatus

# Actions the deterministic layer is currently allowed to execute without a
# human in the loop. Everything else is either blocked or routed to approval.
AUTO_EXECUTABLE_ACTIONS = {
    RecoveryAction.PAYMENT_LINK,
}


@dataclass
class PolicyResult:
    allowed: bool
    requires_approval: bool
    reason: str
    stopped: bool = False


def validate_recovery(payment: PaymentEvent, decision: RecoveryDecision) -> PolicyResult:
    """Deterministic guardrail in front of every recovery action. The LLM only
    diagnoses and recommends; this function is the sole authority on whether
    an action is actually allowed to run, mirroring the receivables policy
    below so every recovery surface (payments, receivables, subscriptions)
    enforces the same stopping rules."""

    if payment.status == PaymentStatus.SUCCESS:
        return PolicyResult(False, False, "Payment is already successful.")

    if decision.action == RecoveryAction.NO_ACTION:
        return PolicyResult(False, False, "Agent selected no action.")

    # Stopping rule: hard cap on repeated outreach/retries per payment.
    if payment.attempt_count >= settings.max_contact_attempts:
        return PolicyResult(
            False, False,
            "Stopping rule triggered: maximum contact/retry attempts reached.",
            stopped=True,
        )

    if decision.action == RecoveryAction.RETRY and payment.attempt_count >= settings.max_retries:
        return PolicyResult(False, False, "Maximum retry limit reached.", stopped=True)

    if payment.amount > settings.max_auto_recovery_amount:
        return PolicyResult(
            False, True,
            "Transaction exceeds automatic recovery limit; requires human approval.",
        )

    if decision.action not in AUTO_EXECUTABLE_ACTIONS:
        return PolicyResult(
            False, False,
            f"Recovery action '{decision.action.value}' is not enabled for "
            "automatic execution in this MVP.",
        )

    return PolicyResult(True, False, "Recovery action passed policy checks.")


# ---------------------------------------------------------------------------
# Receivables (B2B chaser / promise-to-pay) policy: a compliant escalation
# ladder with explicit stopping rules, independent of the LLM payment graph.
# ---------------------------------------------------------------------------

@dataclass
class ChasePolicyResult:
    action: ChaseAction
    reason: str
    escalation_level: int
    stopped: bool = False


def evaluate_receivable(receivable: Receivable, today) -> ChasePolicyResult:
    if receivable.do_not_contact or receivable.status == ReceivableStatus.DO_NOT_CONTACT:
        return ChasePolicyResult(ChaseAction.STOP, "Customer marked do-not-contact.", receivable.escalation_level, stopped=True)

    if receivable.status in {ReceivableStatus.RECOVERED, ReceivableStatus.PARTIALLY_PAID} and receivable.recovered_amount >= receivable.amount:
        return ChasePolicyResult(ChaseAction.NO_ACTION, "Invoice already fully recovered.", receivable.escalation_level)

    # Stopping rule: cooldown between contact attempts.
    if receivable.last_contacted_at is not None:
        hours_since = (
            (_as_utc(today) - _as_utc(receivable.last_contacted_at)).total_seconds() / 3600
        )
        if hours_since < settings.contact_cooldown_hours:
            return ChasePolicyResult(
                ChaseAction.WAIT,
                f"Cooldown active: last contacted {hours_since:.1f}h ago "
                f"(cooldown {settings.contact_cooldown_hours}h).",
                receivable.escalation_level,
            )

    # Honor an active promise-to-pay rather than chasing through it.
    if receivable.promise_to_pay_date is not None and receivable.promise_kept is None:
        if receivable.promise_to_pay_date >= today:
            return ChasePolicyResult(
                ChaseAction.WAIT,
                f"Active promise-to-pay on {receivable.promise_to_pay_date.isoformat()}; honoring it.",
                receivable.escalation_level,
            )
        # Promise date has passed and was never fulfilled -> broken promise, escalate one rung.
        return ChasePolicyResult(
            ChaseAction.ESCALATE_HUMAN,
            "Promise-to-pay date passed without payment; escalating.",
            receivable.escalation_level + 1,
        )

    # Stopping rule: hard cap on outreach attempts -> route to human review
    # instead of continuing to auto-chase.
    if receivable.contact_attempts >= settings.max_contact_attempts:
        return ChasePolicyResult(
            ChaseAction.STOP,
            "Stopping rule triggered: maximum chase attempts reached; routed to human review.",
            receivable.escalation_level,
            stopped=True,
        )

    days_overdue = (today - receivable.due_date).days

    if days_overdue < 0:
        return ChasePolicyResult(ChaseAction.NO_ACTION, "Not yet due.", receivable.escalation_level)

    if days_overdue <= settings.receivable_reminder_days:
        return ChasePolicyResult(ChaseAction.REMINDER, f"{days_overdue}d overdue: gentle reminder.", 1)

    if days_overdue <= settings.receivable_chase_days:
        return ChasePolicyResult(ChaseAction.CHASE_EMAIL, f"{days_overdue}d overdue: active chase.", 2)

    if days_overdue <= settings.receivable_escalate_days:
        return ChasePolicyResult(ChaseAction.VOICE_CALL, f"{days_overdue}d overdue: voice outreach.", 3)

    # Large, very overdue invoices require a human collections owner rather
    # than continued automated contact.
    return ChasePolicyResult(
        ChaseAction.ESCALATE_HUMAN,
        f"{days_overdue}d overdue: past automatic escalation window, needs a human owner.",
        4,
    )


def _as_utc(value):
    from datetime import date, datetime, timezone

    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value
