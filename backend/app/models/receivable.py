from datetime import date, datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ReceivableStatus(str, Enum):
    OPEN = "open"
    OVERDUE = "overdue"
    PROMISED = "promised"
    PARTIALLY_PAID = "partially_paid"
    RECOVERED = "recovered"
    ESCALATED = "escalated"
    DO_NOT_CONTACT = "do_not_contact"
    WRITE_OFF_REVIEW = "write_off_review"


class ChaseAction(str, Enum):
    WAIT = "wait"
    REMINDER = "reminder"
    CHASE_EMAIL = "chase_email"
    VOICE_CALL = "voice_call"
    ESCALATE_HUMAN = "escalate_human"
    STOP = "stop"
    NO_ACTION = "no_action"


class Receivable(BaseModel):
    invoice_id: str
    customer_id: str
    customer_name: str
    customer_email: str | None = None
    customer_contact: str | None = None
    amount: int = Field(gt=0)
    currency: str = "INR"
    due_date: date
    status: ReceivableStatus = ReceivableStatus.OPEN

    contact_attempts: int = 0
    escalation_level: int = 0
    last_contacted_at: datetime | None = None
    do_not_contact: bool = False

    promise_to_pay_date: date | None = None
    promise_to_pay_amount: int | None = None
    promise_kept: bool | None = None

    recovered_amount: int = 0
    payment_link_id: str | None = None
    payment_link: str | None = None
    language_channel: str = "email"  # e.g. email, sms, voice_hinglish

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
