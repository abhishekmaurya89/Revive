from datetime import datetime, timezone
from uuid import uuid4

from app.database import recoveries_collection
from app.models.payment import FailureType, PaymentEvent, PaymentStatus
from app.services.audit import record_audit_event
from app.services.batch_repository import save_batch_run
from app.services.payment_repository import mark_payment_success, save_payment
from app.services.recovery_repository import save_recovery


def _recovered_amount_since(cutoff: datetime) -> int:
    aggregate = list(recoveries_collection.aggregate([
        {"$match": {"status": "recovered", "recovered_at": {"$gte": cutoff}}},
        {"$group": {"_id": None, "total": {"$sum": "$recovered_amount"}}},
    ]))
    return aggregate[0]["total"] if aggregate else 0


def _demo_case(batch_id: str, index: int) -> dict:
    stopped_reasons = [
        ("retry_limit", "Retry limit reached after repeated failures."),
        ("cooldown", "Cooldown active: customer was contacted recently."),
        ("dnc", "Customer is marked do-not-contact."),
        ("ptp_active", "Active promise-to-pay; honoring the commitment."),
    ]
    approval = index in {31, 32, 33, 34, 35, 36, 37}
    stopped = index in {38, 39, 40, 41}
    recovered = index in {0, 1, 2}
    amount = 4_733_333 if recovered else 866_667
    payment_id = f"demo_{batch_id}_{index + 1:03d}"
    source = (
        "failed payment" if index < 20 else
        "abandoned checkout" if index < 28 else
        "overdue invoice" if index < 34 else
        "subscription failure" if index < 38 else
        "promise-to-pay case"
    )
    customer_id = f"cust_{index + 1:03d}"
    payment = PaymentEvent(
        payment_id=payment_id, order_id=f"order_{batch_id}_{index + 1:03d}",
        customer_id=customer_id, amount=amount, status=PaymentStatus.FAILED,
        failure_type=FailureType.CUSTOMER_ACTION if "abandoned" in source else FailureType.TRANSIENT,
        failure_reason=f"{source.title()} requires recovery.", attempt_count=2 if stopped else 0,
        created_at=datetime.now(timezone.utc),
    )
    save_payment(payment)
    diagnosis = {
        "intent": "recover_revenue" if not stopped else "protect_customer_experience",
        "likely_reason": f"{source.title()} detected in the at-risk portfolio.",
        "recoverable": not stopped,
        "evidence": [source, f"Account {customer_id}", "Amount is within portfolio risk window"],
        "confidence": 0.94 if not stopped else 0.99,
    }
    if stopped:
        policy_code, policy_reason = stopped_reasons[index - 38]
        action, outcome = "stop", "stopped"
    elif approval:
        policy_code, policy_reason = "amount_threshold", "Amount threshold exceeded; human approval required."
        action, outcome = "payment_link", "pending_approval"
    else:
        policy_code, policy_reason = "approved", "Passed retry, cooldown, DNC, PTP, and amount checks."
        action = "payment_link" if index < 15 else "reminder" if index < 23 else "voice_call"
        outcome = "executed"
    recovered_amount = amount if recovered else 0
    execution_message = (
        "Payment link created and payment captured." if recovered else
        "Payment link created; awaiting customer payment." if action == "payment_link" and not approval else
        "Reminder sent to the customer." if action == "reminder" else
        "Voice call queued for the collections team." if action == "voice_call" else
        "Held for human approval."
    )
    if recovered:
        mark_payment_success(payment_id, amount)
    recovery_id = f"rec_{batch_id}_{index + 1:03d}"
    save_recovery({
        "recovery_id": recovery_id, "payment_id": payment_id, "order_id": payment.order_id,
        "customer_id": customer_id, "amount": amount, "channel": source,
        "action": action, "status": "recovered" if recovered else outcome, "diagnosis": diagnosis,
        "intent": diagnosis["intent"], "confidence": diagnosis["confidence"], "reason": policy_reason,
        "policy_code": policy_code, "policy_allowed": not approval and not stopped,
        "requires_approval": approval, "policy_reason": policy_reason, "stopped": stopped,
        "execution_success": not approval and not stopped,
        "execution_message": execution_message,
        "recovered_amount": recovered_amount,
        "recovered_at": datetime.now(timezone.utc) if recovered else None,
        "payment_link": f"https://rzp.io/demo/{recovery_id}" if action == "payment_link" and not stopped else None,
        "created_at": datetime.now(timezone.utc),
    })
    for event_type, details in [
        ("diagnosis", diagnosis),
        ("decision", {"action": action, "reason": policy_reason, "confidence": diagnosis["confidence"]}),
        ("policy_check", {"allowed": not approval and not stopped, "requires_approval": approval, "code": policy_code, "reason": policy_reason, "stopped": stopped}),
        ("execution", {"success": not approval and not stopped, "message": execution_message if not stopped else "Action held by policy.", "recovered_amount": recovered_amount}),
    ]:
        record_audit_event("payment", payment_id, event_type, details, actor="revive-agent")
    if recovered:
        record_audit_event("payment", payment_id, "payment_recovered", {"amount": recovered_amount, "batch_id": batch_id}, actor="razorpay-demo")
    return {
        "payment_id": payment_id, "customer_id": customer_id, "order_id": payment.order_id,
        "amount": amount, "source": source, "diagnosis": diagnosis, "action": action,
        "policy_code": policy_code, "policy_reason": policy_reason,
        "policy_allowed": not approval and not stopped, "requires_approval": approval,
        "stopped": stopped, "outcome": outcome, "recovered_amount": recovered_amount,
        "recovery_id": recovery_id,
    }


def run_batch(portfolio_size: int = 42) -> dict:
    """Run diagnosis, deterministic policy, execution, and payment for a demo portfolio."""
    batch_id = f"batch_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc)
    cases = [_demo_case(batch_id, index) for index in range(portfolio_size)]
    recovered_amount = _recovered_amount_since(started_at)
    finished_at = datetime.now(timezone.utc)
    at_risk_amount = sum(case["amount"] for case in cases)
    executed = sum(1 for case in cases if case["policy_allowed"])
    approval_count = sum(1 for case in cases if case["requires_approval"])
    stopped_count = sum(1 for case in cases if case["stopped"])
    record = {
        "batch_id": batch_id, "started_at": started_at, "finished_at": finished_at,
        "portfolio_size": portfolio_size, "at_risk_amount": at_risk_amount,
        "accounts_analyzed": portfolio_size, "eligible_for_automation": executed,
        "requires_approval": approval_count, "stopped": stopped_count,
        "receivables_evaluated": portfolio_size, "receivables_contacted": executed,
        "receivables_escalated": approval_count, "receivables_stopped": stopped_count,
        "action_counts": {
            "payment_link": sum(1 for case in cases if case["action"] == "payment_link"),
            "reminder": sum(1 for case in cases if case["action"] == "reminder"),
            "voice_call": sum(1 for case in cases if case["action"] == "voice_call"),
            "human_approval": approval_count, "stopped": stopped_count,
        },
        "recovered_amount": recovered_amount,
        "recovery_rate": round(recovered_amount / at_risk_amount * 100, 1) if at_risk_amount else 0,
        "prevented_loss": sum(case["amount"] for case in cases if case["policy_allowed"]),
        "results": cases, "cases": cases,
    }
    save_batch_run(record)
    record_audit_event("batch", batch_id, "batch_completed", {
        "accounts_analyzed": portfolio_size, "eligible_for_automation": executed,
        "requires_approval": approval_count, "stopped": stopped_count,
        "recovered_amount": recovered_amount,
    })
    return record
