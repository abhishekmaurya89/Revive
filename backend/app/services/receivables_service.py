from datetime import date, datetime, timezone

from app.models.receivable import ChaseAction, Receivable, ReceivableStatus
from app.services.audit import record_audit_event
from app.services.policy import evaluate_receivable
from app.services.receivables_repository import (
    get_receivable,
    list_open_receivables,
    save_receivable,
    update_receivable_fields,
)

# Chase actions that count as outreach attempts against the stopping-rule cap.
_CONTACT_ACTIONS = {ChaseAction.REMINDER, ChaseAction.CHASE_EMAIL, ChaseAction.VOICE_CALL}

_STATUS_BY_ACTION = {
    ChaseAction.REMINDER: ReceivableStatus.OVERDUE,
    ChaseAction.CHASE_EMAIL: ReceivableStatus.OVERDUE,
    ChaseAction.VOICE_CALL: ReceivableStatus.OVERDUE,
    ChaseAction.ESCALATE_HUMAN: ReceivableStatus.ESCALATED,
    ChaseAction.STOP: ReceivableStatus.WRITE_OFF_REVIEW,
}


def create_receivable(receivable: Receivable) -> dict:
    save_receivable(receivable)
    record_audit_event(
        "receivable", receivable.invoice_id, "created",
        {"amount": receivable.amount, "due_date": receivable.due_date.isoformat()},
    )
    return get_receivable(receivable.invoice_id)


def record_promise_to_pay(invoice_id: str, promise_date: date, amount: int) -> dict | None:
    doc = get_receivable(invoice_id)
    if not doc:
        return None
    update_receivable_fields(
        invoice_id,
        {
            "status": ReceivableStatus.PROMISED.value,
            "promise_to_pay_date": promise_date.isoformat(),
            "promise_to_pay_amount": amount,
            "promise_kept": None,
        },
    )
    record_audit_event(
        "receivable", invoice_id, "promise_to_pay_recorded",
        {"promise_to_pay_date": promise_date.isoformat(), "amount": amount},
    )
    return get_receivable(invoice_id)


def mark_receivable_paid(invoice_id: str, recovered_amount: int) -> dict | None:
    doc = get_receivable(invoice_id)
    if not doc:
        return None
    total_amount = doc["amount"]
    status = ReceivableStatus.RECOVERED if recovered_amount >= total_amount else ReceivableStatus.PARTIALLY_PAID
    update_receivable_fields(
        invoice_id,
        {
            "status": status.value,
            "recovered_amount": recovered_amount,
            "promise_kept": True if doc.get("promise_to_pay_date") else doc.get("promise_kept"),
        },
    )
    record_audit_event(
        "receivable", invoice_id, "payment_recorded",
        {"recovered_amount": recovered_amount, "status": status.value},
    )
    return get_receivable(invoice_id)


def chase_single(invoice_id: str, today: date | None = None) -> dict | None:
    doc = get_receivable(invoice_id)
    if not doc:
        return None

    today = today or date.today()
    receivable = Receivable(**doc)
    decision = evaluate_receivable(receivable, today)

    updates: dict = {}
    if decision.action in _CONTACT_ACTIONS:
        updates["contact_attempts"] = receivable.contact_attempts + 1
        updates["last_contacted_at"] = datetime.now(timezone.utc).isoformat()
    if decision.action in _STATUS_BY_ACTION:
        updates["status"] = _STATUS_BY_ACTION[decision.action].value
    updates["escalation_level"] = decision.escalation_level

    if updates:
        update_receivable_fields(invoice_id, updates)

    record_audit_event(
        "receivable", invoice_id, "chase_evaluated",
        {
            "action": decision.action.value,
            "reason": decision.reason,
            "escalation_level": decision.escalation_level,
            "stopped": decision.stopped,
        },
    )

    return {
        "invoice_id": invoice_id,
        "action": decision.action.value,
        "reason": decision.reason,
        "escalation_level": decision.escalation_level,
        "stopped": decision.stopped,
    }


def chase_batch(today: date | None = None) -> dict:
    today = today or date.today()
    open_receivables = list_open_receivables()

    results = []
    for doc in open_receivables:
        result = chase_single(doc["invoice_id"], today=today)
        if result:
            results.append(result)

    action_counts: dict[str, int] = {}
    for r in results:
        action_counts[r["action"]] = action_counts.get(r["action"], 0) + 1

    return {
        "evaluated": len(results),
        "escalated": action_counts.get(ChaseAction.ESCALATE_HUMAN.value, 0),
        "stopped": action_counts.get(ChaseAction.STOP.value, 0),
        "contacted": sum(
            action_counts.get(a.value, 0) for a in _CONTACT_ACTIONS
        ),
        "action_counts": action_counts,
        "results": results,
    }
