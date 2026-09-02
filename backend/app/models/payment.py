from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"


class FailureType(str, Enum):
    TRANSIENT = "transient"
    BANK_DECLINE = "bank_decline"
    NETWORK = "network"
    CUSTOMER_ACTION = "customer_action"
    UNKNOWN = "unknown"


class PaymentEvent(BaseModel):
    payment_id: str
    order_id: str
    customer_id: str

    amount: int = Field(gt=0)
    currency: str = "INR"

    status: PaymentStatus

    failure_type: FailureType | None = None
    failure_reason: str | None = None

    attempt_count: int = Field(default=0, ge=0)

    created_at: datetime
