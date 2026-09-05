from datetime import datetime, timezone
from uuid import uuid4

from app.database import payments_collection, recoveries_collection
from app.services.audit import record_audit_event
from app.services.batch_repository import save_batch_run


def _real_payment_cases(portfolio_size: int) -> list[dict]:
    payments = payments_collection.find(
        {"status": {"$in": ["failed", "abandoned"]}},
        {"_id": 0},
    ).sort("created_at", -1).limit(portfolio_size)
    cases = []
    for payment in payments:
        recovery = recoveries_collection.find_one(
            {"payment_id": payment.get("payment_id")},
            {"_id": 0},
        ) or {}
        cases.append({
            "payment_id": payment.get("payment_id"),
            "customer_id": payment.get("customer_id", "unknown"),
            "order_id": payment.get("order_id", "unknown"),
            "amount": payment.get("amount", 0),
            "source": payment.get("failure_type", payment.get("status", "unknown")),
            "diagnosis": recovery.get("diagnosis", {
                "likely_reason": payment.get("failure_reason") or "Razorpay payment event",
                "confidence": recovery.get("confidence", 0),
            }),
            "action": recovery.get("action"),
            "policy_code": recovery.get("policy_code"),
            "policy_reason": recovery.get("policy_reason") or recovery.get("reason"),
            "policy_allowed": recovery.get("policy_allowed", False),
            "requires_approval": recovery.get("requires_approval", False),
            "stopped": recovery.get("stopped", False),
            "outcome": recovery.get("status"),
            "recovered_amount": recovery.get("recovered_amount", 0),
        })
    return cases


def run_batch(portfolio_size: int = 42) -> dict:
    """Summarize real failed payment events received from Razorpay."""
    batch_id = f"batch_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc)
    cases = _real_payment_cases(portfolio_size)
    finished_at = datetime.now(timezone.utc)
    at_risk_amount = sum(case["amount"] for case in cases)
    recovered_amount = sum(case["recovered_amount"] for case in cases)
    executed = sum(1 for case in cases if case["policy_allowed"])
    approval_count = sum(1 for case in cases if case["requires_approval"])
    stopped_count = sum(1 for case in cases if case["stopped"])
    record = {
        "batch_id": batch_id, "started_at": started_at, "finished_at": finished_at,
        "portfolio_size": len(cases), "at_risk_amount": at_risk_amount,
        "accounts_analyzed": len(cases), "eligible_for_automation": executed,
        "requires_approval": approval_count, "stopped": stopped_count,
        "recovered_amount": recovered_amount,
        "recovery_rate": round(recovered_amount / at_risk_amount * 100, 1) if at_risk_amount else 0,
        "prevented_loss": sum(case["amount"] for case in cases if case["policy_allowed"]),
        "results": cases, "cases": cases, "source": "razorpay_webhooks",
    }
    save_batch_run(record)
    record_audit_event("batch", batch_id, "batch_completed", {
        "accounts_analyzed": len(cases), "eligible_for_automation": executed,
        "requires_approval": approval_count, "stopped": stopped_count,
        "recovered_amount": recovered_amount, "source": "razorpay_webhooks",
    })
    return record
