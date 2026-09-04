from datetime import datetime, timezone

from app.models.payment import FailureType, PaymentEvent, PaymentStatus
from app.services.recovery_flow import process_payment_event
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class CheckoutAbandonedIn(BaseModel):
    order_id: str
    customer_id: str
    amount: int = Field(gt=0)
    currency: str = "INR"


class SubscriptionFailedIn(BaseModel):
    subscription_id: str
    customer_id: str
    amount: int = Field(gt=0)
    currency: str = "INR"
    attempt_count: int = 1
    failure_reason: str | None = None


@router.post("/checkout-abandoned")
async def checkout_abandoned(payload: CheckoutAbandonedIn):
    """Ingest a checkout-drop-off signal (e.g. from client-side analytics)
    and run it through the same detect -> diagnose -> recover -> audit loop
    used for failed payments."""
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
    )
    return await process_payment_event(payment)


@router.post("/subscription-failed")
async def subscription_failed(payload: SubscriptionFailedIn):
    """Ingest a recurring-payment / mandate failure from a billing system so
    it can be triaged for a mandate retry, payment link, or escalation."""
    payment = PaymentEvent(
        payment_id=f"sub_{payload.subscription_id}_{payload.attempt_count}",
        order_id=payload.subscription_id,
        customer_id=payload.customer_id,
        amount=payload.amount,
        currency=payload.currency,
        status=PaymentStatus.FAILED,
        failure_type=FailureType.TRANSIENT,
        failure_reason=payload.failure_reason or "Subscription mandate charge failed.",
        attempt_count=payload.attempt_count,
        created_at=datetime.now(timezone.utc),
    )
    return await process_payment_event(payment)
