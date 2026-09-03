import json

from app.config import settings
from app.services.razorpay_client import client
from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
):
    """
    Receives Razorpay webhook events.

    The webhook signature must be verified before
    trusting the event payload.
    """

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

    if event_type == "payment.captured":
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})

        payment_id = payment_entity.get("id")
        amount = payment_entity.get("amount")

        print(f"Payment captured: {payment_id}, amount={amount}")

        return {
            "status": "processed",
            "event": event_type,
            "payment_id": payment_id,
            "amount": amount,
        }

    return {
        "status": "ignored",
        "event": event_type,
    }
