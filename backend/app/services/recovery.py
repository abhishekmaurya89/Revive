from uuid import uuid4

from app.agents.schemas import RecoveryAction
from app.models.payment import PaymentEvent
from app.services.razorpay_client import client


def execute_recovery(
    payment: PaymentEvent,
    action: RecoveryAction,
):
    recovery_id = f"rec_{uuid4().hex[:12]}"

    if action == RecoveryAction.PAYMENT_LINK:
        response = client.payment_link.create(
            {
                "amount": payment.amount,
                "currency": payment.currency,
                "description": f"Recovery for {payment.order_id}",
                "customer": {
                    "name": payment.customer_id,
                },
                "notify": {
                    "sms": False,
                    "email": False,
                },
                "notes": {
                    "recovery_id": recovery_id,
                    "payment_id": payment.payment_id,
                    "order_id": payment.order_id,
                },
            }
        )

        return {
            "success": True,
            "action": action.value,
            "message": "Payment link created.",
            "payment_link": response.get("short_url"),
            "payment_link_id": response.get("id"),
            "recovery_id": recovery_id,
            "recovered_amount": 0,
        }

    return {
        "success": False,
        "action": action.value,
        "message": "Recovery action not connected.",
        "recovery_id": recovery_id,
        "recovered_amount": 0,
    }
