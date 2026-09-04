from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RecoveryRecord(BaseModel):
    recovery_id: str
    payment_id: str
    order_id: str
    amount: int
    currency: str = "INR"
    action: str
    status: str = "created"
    payment_link_id: str | None = None
    payment_link: str | None = None
    recovered_amount: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recovered_at: datetime | None = None
