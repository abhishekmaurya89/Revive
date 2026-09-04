from datetime import datetime, timezone

from app.database import payments_collection
from app.models.payment import PaymentEvent


def save_payment(payment: PaymentEvent) -> None:
    document = payment.model_dump(mode="json")
    document["updated_at"] = datetime.now(timezone.utc)

    payments_collection.update_one(
        {"payment_id": payment.payment_id},
        {"$set": document},
        upsert=True,
    )


def mark_payment_success(payment_id: str, amount: int | None = None) -> None:
    update = {
        "status": "success",
        "updated_at": datetime.now(timezone.utc),
    }
    if amount is not None:
        update["captured_amount"] = amount

    payments_collection.update_one(
        {"payment_id": payment_id},
        {"$set": update},
    )
