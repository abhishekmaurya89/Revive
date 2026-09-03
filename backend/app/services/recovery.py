from uuid import uuid4

from app.agents.schemas import RecoveryAction
from app.models.payment import PaymentEvent
from app.services.recovery_repository import save_recovery
from app.services.razorpay_client import client


async def execute_recovery(
    payment: PaymentEvent,
    action: RecoveryAction,
):

    if action == RecoveryAction.PAYMENT_LINK:
        recovery_id = f"rec_{uuid4().hex[:12]}"

        response = client.payment_link.create(
            {
                "amount": payment.amount,
                "currency": payment.currency,
                "description": (f"Recovery for {payment.order_id}"),
                "customer": {
                    "name": payment.customer_id,
                },
                "notify": {
                    "sms": False,
                    "email": False,
                },
                "notes": {
                    "recovery_id": recovery_id,
                    "order_id": payment.order_id,
                    "payment_id": payment.payment_id,
                },
            }
        )

        payment_link_id = response.get("id")
        payment_link = response.get("short_url")

        await save_recovery(
            {
                "recovery_id": recovery_id,
                "payment_id": payment.payment_id,
                "order_id": payment.order_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "action": action.value,
                "status": "payment_link_created",
                "payment_link_id": payment_link_id,
                "payment_link": payment_link,
                "recovered_amount": 0,
            }
        )

        return {
            "success": True,
            "action": action.value,
            "message": "Payment link created.",
            "payment_link": payment_link,
            "payment_link_id": payment_link_id,
            "recovery_id": recovery_id,
            "recovered_amount": 0,
        }

    return {
        "success": False,
        "action": action.value,
        "message": ("Recovery action not connected to a Razorpay API."),
        "recovered_amount": 0,
    }
