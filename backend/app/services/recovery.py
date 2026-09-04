from uuid import uuid4

from app.agents.schemas import RecoveryAction
from app.models.payment import PaymentEvent
from app.services.recovery_repository import save_recovery
from app.services.razorpay_client import client


async def execute_recovery(payment: PaymentEvent, action: RecoveryAction) -> dict:
    if action == RecoveryAction.PAYMENT_LINK:
        recovery_id = f"rec_{uuid4().hex[:12]}"

        response = client.payment_link.create(
            {
                "amount": payment.amount,
                "currency": payment.currency,
                "description": f"Recovery for {payment.order_id}",
                "reference_id": recovery_id,
                "customer": {
                    "name": payment.customer_id,
                },
                "notify": {
                    "sms": False,
                    "email": False,
                },
                "reminder_enable": False,
                "notes": {
                    "recovery_id": recovery_id,
                    "order_id": payment.order_id,
                    "payment_id": payment.payment_id,
                },
            }
        )

        payment_link_id = response.get("id")
        payment_link = response.get("short_url")

        if not payment_link_id or not payment_link:
            return {
                "success": False,
                "action": action.value,
                "message": "Razorpay did not return a payment link.",
                "recovered_amount": 0,
            }

        save_recovery(
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
        "message": f"Recovery action '{action.value}' is not connected to an execution provider.",
        "recovered_amount": 0,
    }
