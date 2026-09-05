from datetime import datetime, timezone

from app.database import recoveries_collection


def recovery_exists(payment_id: str) -> bool:
    return recoveries_collection.find_one(
        {"payment_id": payment_id},
        {"_id": 1},
    ) is not None


def save_recovery(record: dict) -> None:
    record = dict(record)
    record.setdefault("created_at", datetime.now(timezone.utc))

    recoveries_collection.update_one(
        {"recovery_id": record["recovery_id"]},
        {"$set": record},
        upsert=True,
    )


def mark_recovered(
    payment_link_id: str,
    payment_id: str | None,
    recovered_amount: int,
) -> None:
    recoveries_collection.update_one(
        {"payment_link_id": payment_link_id},
        {
            "$set": {
                "status": "recovered",
                "payment_id": payment_id,
                "recovered_amount": recovered_amount,
                "recovered_at": datetime.now(timezone.utc),
            }
        },
    )


def mark_recovered_by_payment_id(payment_id: str, recovered_amount: int) -> bool:
    result = recoveries_collection.update_one(
        {"payment_id": payment_id},
        {
            "$set": {
                "status": "recovered",
                "recovered_amount": recovered_amount,
                "recovered_at": datetime.now(timezone.utc),
            }
        },
    )
    return result.matched_count > 0
