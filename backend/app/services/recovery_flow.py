from datetime import datetime, timezone

from app.agents.recovery_graph import build_recovery_graph
from app.models.payment import PaymentEvent
from app.services.audit import record_audit_event
from app.services.payment_repository import save_payment
from app.services.recovery_repository import recovery_exists, save_recovery

recovery_graph = build_recovery_graph()


async def process_payment_event(payment: PaymentEvent) -> dict:
    """Single entry point for every revenue-at-risk payment signal, whether
    it originates from a Razorpay webhook, a checkout-abandonment beacon, or
    a subscription/mandate failure feed. Runs the LangGraph agent, enforces
    policy + stopping rules, executes the allowed action, and writes a full
    audit trail."""

    if recovery_exists(payment.payment_id):
        return {"status": "already_processed", "payment_id": payment.payment_id}

    save_payment(payment)
    record_audit_event(
        "payment", payment.payment_id, "event_received",
        {"status": payment.status.value, "amount": payment.amount, "failure_type": payment.failure_type},
    )

    result = await recovery_graph.ainvoke({"payment": payment})
    decision = result.get("decision")
    diagnosis = result.get("diagnosis")

    if diagnosis:
        record_audit_event("payment", payment.payment_id, "diagnosis", diagnosis.model_dump())
    if decision:
        record_audit_event("payment", payment.payment_id, "decision", decision.model_dump())

    record_audit_event(
        "payment", payment.payment_id, "policy_check",
        {
            "allowed": result.get("policy_allowed"),
            "requires_approval": result.get("requires_approval"),
            "reason": result.get("policy_reason"),
            "stopped": result.get("stopped", False),
        },
    )
    record_audit_event(
        "payment", payment.payment_id, "execution",
        {
            "success": result.get("execution_success"),
            "message": result.get("execution_message"),
            "recovered_amount": result.get("recovered_amount", 0),
        },
    )

    recovery_id = result.get("recovery_id") or f"pending_{payment.payment_id}"
    save_recovery(
        {
            "recovery_id": recovery_id,
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "subscription_id": payment.subscription_id,
            "channel": payment.status.value,
            "action": decision.action.value if decision else None,
            "confidence": decision.confidence if decision else None,
            "reason": decision.reason if decision else None,
            "policy_allowed": result.get("policy_allowed"),
            "requires_approval": result.get("requires_approval"),
            "policy_reason": result.get("policy_reason"),
            "stopped": result.get("stopped", False),
            "execution_success": result.get("execution_success"),
            "execution_message": result.get("execution_message"),
            "recovered_amount": result.get("recovered_amount", 0),
            "payment_link": result.get("payment_link"),
            "payment_link_id": result.get("payment_link_id"),
            "created_at": datetime.now(timezone.utc),
        }
    )

    return {
        "status": "processed",
        "payment_id": payment.payment_id,
        "recovery": {
            "recovery_id": recovery_id,
            "action": decision.action.value if decision else None,
            "confidence": decision.confidence if decision else None,
            "reason": decision.reason if decision else None,
            "diagnosis": diagnosis.model_dump() if diagnosis else None,
            "policy_allowed": result.get("policy_allowed"),
            "requires_approval": result.get("requires_approval"),
            "policy_reason": result.get("policy_reason"),
            "stopped": result.get("stopped", False),
            "execution_success": result.get("execution_success"),
            "execution_message": result.get("execution_message"),
            "payment_link": result.get("payment_link"),
        },
    }
