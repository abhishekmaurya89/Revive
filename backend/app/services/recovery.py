from app.agents.schemas import RecoveryAction
from app.models.payment import PaymentEvent
from app.services.razorpay_client import client


def execute_recovery(
    payment: PaymentEvent,
    action: RecoveryAction,
):

    if action == RecoveryAction.PAYMENT_LINK:

        response = client.payment_link.create({
            "amount": payment.amount,
            "currency": payment.currency,
            "description": (
                f"Recovery for {payment.order_id}"
            ),
            "customer": {
                "name": payment.customer_id,
            },
            "notify": {
                "sms": False,
                "email": False,
            },
        })

        return {
            "success": True,
            "action": action.value,
            "message": "Payment link created.",
            "payment_link": response.get("short_url"),
            "recovered_amount": 0,
        }

    return {
        "success": False,
        "action": action.value,
        "message": (
            "Recovery action not yet connected "
            "to a Razorpay API."
        ),
        "recovered_amount": 0,
    }