from app.services.audit import get_audit_trail, list_recent_audit_events
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def recent_audit_events(limit: int = 200):
    return {"audit_trail": list_recent_audit_events(limit=limit)}


@router.get("/{entity_id}")
async def audit_for_entity(entity_id: str):
    return {"audit_trail": get_audit_trail(entity_id)}
