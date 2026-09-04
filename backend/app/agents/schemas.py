from enum import Enum

from pydantic import BaseModel, Field


class RecoveryAction(str, Enum):
    RETRY = "retry"
    PAYMENT_LINK = "payment_link"
    REMINDER = "reminder"
    MANDATE_RETRY = "mandate_retry"
    VOICE_CALL = "voice_call"
    ESCALATE = "escalate"
    NO_ACTION = "no_action"


class RecoveryDecision(BaseModel):
    action: RecoveryAction
    reason: str = Field(description="Concise explanation for the selected recovery action")
    confidence: float = Field(ge=0.0, le=1.0)


class Diagnosis(BaseModel):
    likely_reason: str
    recoverable: bool
    evidence: list[str] = Field(default_factory=list)
