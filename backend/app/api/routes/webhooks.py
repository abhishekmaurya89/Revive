import json
from datetime import datetime, timezone

from app.agents.recovery_graph import build_recovery_graph
from app.config import settings
from app.database import payments_collection, recoveries_collection
from app.models.payment import PaymentEvent, PaymentStatus
from app.services.razorpay_client import client
from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()

recovery_graph = build_recovery_graph()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
):
    body = await request.body()

    if not x_razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing Razorpay signature",
        )

    try:
        client.utility.verify_webhook_signature(
            body.decode("utf-8"),
            x_razorpay_signature,
            settings.razorpay_webhook_secret,
        )
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature",
        )

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    event_type = event.get("event")

    print(f"Received Razorpay event: {event_type}")

    if event_type != "payment.failed":
        return {
            "status": "ignored",
            "event": event_type,
        }

    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})

    payment_id = payment_entity.get("id")
    amount = payment_entity.get("amount")
    currency = payment_entity.get("currency", "INR")

    if not payment_id or amount is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment payload",
        )

    created_at_timestamp = payment_entity.get("created_at")

    if created_at_timestamp:
        created_at = datetime.fromtimestamp(
            created_at_timestamp,
            tz=timezone.utc,
        )
    else:
        created_at = datetime.now(timezone.utc)

    payment = PaymentEvent(
        payment_id=payment_id,
        order_id=payment_entity.get("order_id") or "unknown",
        customer_id=(
            payment_entity.get("email") or payment_entity.get("contact") or "unknown"
        ),
        amount=amount,
        currency=currency,
        status=PaymentStatus.FAILED,
        attempt_count=1,
        failure_type=None,
        failure_reason=payment_entity.get("error_description"),
        created_at=created_at,
    )

    payments_collection.update_one(
        {"payment_id": payment.payment_id},
        {
            "$set": {
                **payment.model_dump(mode="json"),
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    result = await recovery_graph.ainvoke(
        {
            "payment": payment,
        }
    )

    decision = result.get("decision")

    recovery_document = {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "action": decision.action.value if decision else None,
        "confidence": decision.confidence if decision else None,
        "reason": decision.reason if decision else None,
        "policy_allowed": result.get("policy_allowed"),
        "requires_approval": result.get("requires_approval"),
        "policy_reason": result.get("policy_reason"),
        "execution_success": result.get("execution_success"),
        "execution_message": result.get("execution_message"),
        "recovered_amount": result.get("recovered_amount", 0),
        "recovery_id": result.get("recovery_id"),
        "payment_link": result.get("payment_link"),
        "payment_link_id": result.get("payment_link_id"),
        "created_at": datetime.now(timezone.utc),
    }

    recoveries_collection.insert_one(recovery_document)

    return {
        "status": "processed",
        "event": event_type,
        "payment_id": payment_id,
        "recovery": {
            "action": decision.action.value if decision else None,
            "execution_success": result.get("execution_success"),
            "execution_message": result.get("execution_message"),
            "payment_link": result.get("payment_link"),
            "recovery_id": result.get("recovery_id"),
        },
    }
