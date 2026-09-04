from typing import TypedDict

from app.agents.schemas import Diagnosis, RecoveryDecision
from app.models.payment import PaymentEvent


class RecoveryState(TypedDict, total=False):
    payment: PaymentEvent
    diagnosis: Diagnosis
    decision: RecoveryDecision
    policy_allowed: bool
    requires_approval: bool
    policy_reason: str
    stopped: bool
    execution_success: bool
    execution_message: str
    recovered_amount: int
    payment_link: str
    payment_link_id: str
    recovery_id: str
