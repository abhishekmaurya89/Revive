from app.database import batch_runs_collection


def save_batch_run(record: dict) -> None:
    batch_runs_collection.update_one(
        {"batch_id": record["batch_id"]},
        {"$set": record},
        upsert=True,
    )


def list_batch_runs(limit: int = 50) -> list[dict]:
    return list(
        batch_runs_collection.find({}, {"_id": 0}).sort("started_at", -1).limit(limit)
    )


def get_batch_run(batch_id: str) -> dict | None:
    return batch_runs_collection.find_one({"batch_id": batch_id}, {"_id": 0})
