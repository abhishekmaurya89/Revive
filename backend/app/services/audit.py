from datetime import datetime, timezone
from uuid import uuid4

from app.database import audit_collection


def record_audit_event(
    entity_type: str,
    entity_id: str,
    event_type: str,
    details: dict,
    actor: str = "system",
) -> dict:
    """Append-only audit trail entry. Every automated decision, policy
    outcome, stopping-rule trigger and executed action must be recorded here
    so recovery activity across a batch can be reconstructed and reviewed."""
    event = {
        "audit_id": f"audit_{uuid4().hex[:12]}",
        "entity_type": entity_type,  # "payment" | "receivable" | "batch"
        "entity_id": entity_id,
        "event_type": event_type,
        "actor": actor,
        "details": details,
        "timestamp": datetime.now(timezone.utc),
    }
    audit_collection.insert_one(dict(event))
    event.pop("_id", None)
    return event


def get_audit_trail(entity_id: str, entity_type: str | None = None) -> list[dict]:
    query: dict = {"entity_id": entity_id}
    if entity_type:
        query["entity_type"] = entity_type
    return list(
        audit_collection.find(query, {"_id": 0}).sort("timestamp", 1)
    )


def list_recent_audit_events(limit: int = 200) -> list[dict]:
    return list(
        audit_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    )
