from datetime import datetime, timezone


def create_audit_event(
    payment_id: str,
    event_type: str,
    details: dict,
):
    return {
        "payment_id": payment_id,
        "event_type": event_type,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }