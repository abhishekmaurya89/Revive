from uuid import uuid4

from app.agents.schemas import RecoveryAction
from app.models.payment import PaymentEvent


class RecoveryResult:
    def __init__(
        self,
        success: bool,
        action: RecoveryAction,
        message: str,
        recovered_amount: int = 0,
    ):
        self.success = success
        self.action = action
        self.message = message
        self.recovered_amount = recovered_amount


def execute_recovery(
    payment: PaymentEvent,
    action: RecoveryAction,
) -> RecoveryResult:

    if action == RecoveryAction.RETRY:
        return RecoveryResult(
            success=True,
            action=action,
            message="Payment retry succeeded.",
            recovered_amount=payment.amount,
        )

    if action == RecoveryAction.PAYMENT_LINK:
        link_id = uuid4().hex[:12]

        return RecoveryResult(
            success=True,
            action=action,
            message=f"Payment link created: {link_id}",
        )

    if action == RecoveryAction.REMINDER:
        return RecoveryResult(
            success=True,
            action=action,
            message="Recovery reminder queued.",
        )

    return RecoveryResult(
        success=False,
        action=action,
        message="No executable recovery action.",
    )
