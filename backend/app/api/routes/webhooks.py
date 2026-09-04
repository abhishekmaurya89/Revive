import json
from datetime import datetime, timezone

from app.config import settings
from app.models.payment import FailureType, PaymentEvent, PaymentStatus
from app.services.payment_repository import mark_payment_success
from app.services.recovery_flow import process_payment_event
from app.services.recovery_repository import mark_recovered, recovery_exists
from app.services.razorpay_client import client
from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


def map_failure_type(entity: dict) -> FailureType:
    code = str(entity.get("error_code") or "").lower()
    source = str(entity.get("error_source") or "").lower()
    step = str(entity.get("error_step") or "").lower()

    if any(value in code for value in ("timeout", "server_error", "gateway")):
        return FailureType.NETWORK
    if source in {"bank", "issuer"}:
        return FailureType.BANK_DECLINE
    if source in {"customer", "request"} or step in {"payment_authentication", "payment_initiation"}:
        return FailureType.CUSTOMER_ACTION
    if any(value in code for value in ("temporary", "retry", "rate_limit")):
        return FailureType.TRANSIENT
    return FailureType.UNKNOWN


def verify_signature(body: bytes, signature: str | None) -> None:
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Razorpay signature")
    try:
        client.utility.verify_webhook_signature(
            body.decode("utf-8"),
            signature,
            settings.razorpay_webhook_secret,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
):
    body = await request.body()
    verify_signature(body, x_razorpay_signature)

    try:
        event = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    event_type = event.get("event")

    if event_type in {"payment.captured", "payment.authorized", "order.paid"}:
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        payment_id = payment_entity.get("id")
        amount = payment_entity.get("amount")
        if payment_id:
            mark_payment_success(payment_id, amount)
        return {"status": "processed", "event": event_type, "payment_id": payment_id}

    if event_type == "payment_link.paid":
        payload = event.get("payload", {})
        link_entity = payload.get("payment_link", {}).get("entity", {})
        payment_entity = payload.get("payment", {}).get("entity", {})
        payment_link_id = link_entity.get("id")
        payment_id = payment_entity.get("id")
        amount = payment_entity.get("amount") or link_entity.get("amount_paid") or 0

        if payment_link_id:
            mark_recovered(payment_link_id, payment_id, amount)
        if payment_id:
            mark_payment_success(payment_id, amount)

        return {
            "status": "processed",
            "event": event_type,
            "payment_id": payment_id,
            "payment_link_id": payment_link_id,
            "recovered_amount": amount,
        }

    if event_type != "payment.failed":
        return {"status": "ignored", "event": event_type}

    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id")
    amount = payment_entity.get("amount")

    if not payment_id or amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid payment payload")

    if recovery_exists(payment_id):
        return {"status": "already_processed", "event": event_type, "payment_id": payment_id}

    created_at = payment_entity.get("created_at")
    created_datetime = (
        datetime.fromtimestamp(created_at, tz=timezone.utc)
        if created_at
        else datetime.now(timezone.utc)
    )

    payment = PaymentEvent(
        payment_id=payment_id,
        order_id=payment_entity.get("order_id") or "unknown",
        customer_id=(
            payment_entity.get("customer_id")
            or payment_entity.get("email")
            or payment_entity.get("contact")
            or "unknown"
        ),
        amount=amount,
        currency=payment_entity.get("currency", "INR"),
        status=PaymentStatus.FAILED,
        attempt_count=1,
        failure_type=map_failure_type(payment_entity),
        failure_reason=payment_entity.get("error_description"),
        created_at=created_datetime,
    )

    result = await process_payment_event(payment)
    return {"status": result["status"], "event": event_type, **result}
