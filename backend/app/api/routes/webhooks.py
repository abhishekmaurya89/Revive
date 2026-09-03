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
    Receives and verifies Razorpay webhook events.

    Current recovery flow:
        payment_link.paid
            ↓
        identify recovery
            ↓
        mark revenue recovered

    The webhook signature is verified before
    trusting the payload.
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

    print(f"\n[Razorpay Webhook] Event: {event_type}")

    if event_type == "payment_link.paid":
        payment_link_entity = (
            event.get("payload", {}).get("payment_link", {}).get("entity", {})
        )

        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})

        payment_link_id = payment_link_entity.get("id")
        payment_id = payment_entity.get("id")

        amount = payment_link_entity.get("amount", 0)

        notes = payment_link_entity.get(
            "notes",
            {},
        )

        recovery_id = notes.get("recovery_id")

        order_id = notes.get("order_id")

        print("\n[Recovery Successful]")

        print(f"Recovery ID:     {recovery_id}")

        print(f"Payment Link:    {payment_link_id}")

        print(f"Payment ID:      {payment_id}")

        print(f"Amount:          ₹{amount / 100:.2f}")

        print(f"Order ID:        {order_id}")

        return {
            "status": "processed",
            "event": event_type,
            "recovery_id": recovery_id,
            "payment_link_id": payment_link_id,
            "payment_id": payment_id,
            "order_id": order_id,
            "recovered_amount": amount,
        }

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

    print(f"[Razorpay Webhook] Ignored event: {event_type}")

    return {
        "status": "ignored",
        "event": event_type,
    }
