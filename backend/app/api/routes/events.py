import secrets
from datetime import datetime, timezone

from app.config import settings
from app.models.payment import FailureType, PaymentEvent, PaymentStatus
from app.services.recovery_flow import process_payment_event
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class CheckoutAbandonedIn(BaseModel):
    order_id: str
    customer_id: str
    amount: int = Field(gt=0)
    currency: str = "INR"
    customer_email: str | None = None
    customer_contact: str | None = None


@router.post("/checkout-abandoned")
async def checkout_abandoned(
    payload: CheckoutAbandonedIn,
    x_checkout_event_key: str | None = Header(default=None),
):
    """Ingest an authenticated checkout event from the merchant checkout."""
    if not settings.checkout_event_secret:
        raise HTTPException(status_code=503, detail="Checkout event integration is not configured")
    if not x_checkout_event_key or not secrets.compare_digest(
        x_checkout_event_key, settings.checkout_event_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid checkout event key")

    payment = PaymentEvent(
        payment_id=f"abandon_{payload.order_id}",
        order_id=payload.order_id,
        customer_id=payload.customer_id,
        amount=payload.amount,
        currency=payload.currency,
        status=PaymentStatus.ABANDONED,
        failure_type=FailureType.CUSTOMER_ACTION,
        failure_reason="Checkout abandoned before payment was submitted.",
        attempt_count=0,
        created_at=datetime.now(timezone.utc),
        customer_email=payload.customer_email,
        customer_contact=payload.customer_contact,
    )
    return await process_payment_event(payment)
