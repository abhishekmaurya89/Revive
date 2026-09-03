from datetime import datetime, timezone


async def save_recovery(record: dict):
    await recovery_collection.update_one(
        {
            "recovery_id": record["recovery_id"],
        },
        {
            "$set": record,
        },
        upsert=True,
    )


async def mark_recovered(
    recovery_id: str,
    payment_id: str | None,
    recovered_amount: int,
):
    await recovery_collection.update_one(
        {
            "recovery_id": recovery_id,
        },
        {
            "$set": {
                "status": "recovered",
                "payment_id": payment_id,
                "recovered_amount": recovered_amount,
                "recovered_at": datetime.now(timezone.utc),
            }
        },
    )
