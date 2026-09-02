from enum import Enum

from pydantic import BaseModel, Field


class RecoveryAction(str, Enum):
    RETRY = "retry"
    PAYMENT_LINK = "payment_link"
    REMINDER = "reminder"
    ESCALATE = "escalate"
    NO_ACTION = "no_action"


class RecoveryDecision(BaseModel):
    action: RecoveryAction

    reason: str = Field(
        description="Concise explanation for the selected recovery action"
    )

    confidence: float = Field(ge=0.0, le=1.0)
