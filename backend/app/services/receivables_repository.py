from datetime import datetime, timezone

from app.database import receivables_collection
from app.models.receivable import Receivable


def save_receivable(receivable: Receivable) -> None:
    document = receivable.model_dump(mode="json")
    document["updated_at"] = datetime.now(timezone.utc).isoformat()
    receivables_collection.update_one(
        {"invoice_id": receivable.invoice_id},
        {"$set": document},
        upsert=True,
    )


def get_receivable(invoice_id: str) -> dict | None:
    return receivables_collection.find_one({"invoice_id": invoice_id}, {"_id": 0})


def list_receivables(status: str | None = None, limit: int = 200) -> list[dict]:
    query = {"status": status} if status else {}
    return list(
        receivables_collection.find(query, {"_id": 0}).sort("due_date", 1).limit(limit)
    )


def list_open_receivables(limit: int = 500) -> list[dict]:
    return list(
        receivables_collection.find(
            {"status": {"$nin": ["recovered", "write_off_review"]}}, {"_id": 0}
        ).limit(limit)
    )


def update_receivable_fields(invoice_id: str, fields: dict) -> None:
    fields = dict(fields)
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    receivables_collection.update_one({"invoice_id": invoice_id}, {"$set": fields})


def mark_receivable_recovered(invoice_id: str, recovered_amount: int) -> bool:
    receivable = get_receivable(invoice_id)
    if not receivable:
        return False
    total_amount = receivable["amount"]
    status = "recovered" if recovered_amount >= total_amount else "partially_paid"
    update_receivable_fields(
        invoice_id,
        {"status": status, "recovered_amount": recovered_amount},
    )
    return True
