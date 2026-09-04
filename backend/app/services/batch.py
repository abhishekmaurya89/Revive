from datetime import datetime, timezone
from uuid import uuid4

from app.database import recoveries_collection
from app.services.audit import record_audit_event
from app.services.batch_repository import save_batch_run
from app.services.receivables_service import chase_batch


def _recovered_amount_since(cutoff: datetime) -> int:
    pipeline = [
        {"$match": {"status": "recovered", "recovered_at": {"$gte": cutoff}}},
        {"$group": {"_id": None, "total": {"$sum": "$recovered_amount"}}},
    ]
    aggregate = list(recoveries_collection.aggregate(pipeline))
    return aggregate[0]["total"] if aggregate else 0


def run_batch() -> dict:
    """Runs the receivables escalation sweep for this cycle and reports the
    measured money recovered across the batch, alongside how many items were
    escalated or stopped, and writes the whole thing to the audit trail."""
    batch_id = f"batch_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc)

    receivables_result = chase_batch()
    recovered_amount = _recovered_amount_since(started_at)

    finished_at = datetime.now(timezone.utc)
    record = {
        "batch_id": batch_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "receivables_evaluated": receivables_result["evaluated"],
        "receivables_contacted": receivables_result["contacted"],
        "receivables_escalated": receivables_result["escalated"],
        "receivables_stopped": receivables_result["stopped"],
        "action_counts": receivables_result["action_counts"],
        "recovered_amount": recovered_amount,
        "results": receivables_result["results"],
    }
    save_batch_run(record)
    record_audit_event(
        "batch", batch_id, "batch_completed",
        {
            "receivables_evaluated": receivables_result["evaluated"],
            "receivables_escalated": receivables_result["escalated"],
            "receivables_stopped": receivables_result["stopped"],
            "recovered_amount": recovered_amount,
        },
    )
    return record
