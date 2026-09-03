from typing import TypedDict

from app.agents.schemas import RecoveryDecision
from app.models.payment import PaymentEvent


class RecoveryState(TypedDict, total=False):
    payment: PaymentEvent

    diagnosis: str
    decision: RecoveryDecision

    policy_allowed: bool
    requires_approval: bool
    policy_reason: str

    execution_success: bool
    execution_message: str
    recovered_amount: int

    audit_events: list[dict]