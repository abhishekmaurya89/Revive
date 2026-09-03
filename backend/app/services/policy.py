from dataclasses import dataclass

from app.agents.schemas import RecoveryAction, RecoveryDecision
from app.models.payment import PaymentEvent

MAX_AUTO_RECOVERY_AMOUNT = 10_000
MAX_RETRIES = 2


@dataclass
class PolicyResult:
    allowed: bool
    requires_approval: bool
    reason: str


def validate_recovery(
    payment: PaymentEvent,
    decision: RecoveryDecision,
) -> PolicyResult:

    if payment.status.value == "success":
        return PolicyResult(
            allowed=False,
            requires_approval=False,
            reason="Payment is already successful.",
        )

    if (
        decision.action == RecoveryAction.RETRY
        and payment.attempt_count >= MAX_RETRIES
    ):
        return PolicyResult(
            allowed=False,
            requires_approval=False,
            reason="Maximum retry limit reached.",
        )

    if payment.amount > MAX_AUTO_RECOVERY_AMOUNT:
        return PolicyResult(
            allowed=False,
            requires_approval=True,
            reason="Transaction exceeds automatic recovery limit.",
        )


    if decision.action == RecoveryAction.NO_ACTION:
        return PolicyResult(
            allowed=False,
            requires_approval=False,
            reason="Agent selected no action.",
        )

    return PolicyResult(
        allowed=True,
        requires_approval=False,
        reason="Recovery action passed policy checks.",
    )