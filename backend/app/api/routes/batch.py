from app.services.audit import get_audit_trail, list_recent_audit_events
from app.services.batch import run_batch
from app.services.batch_repository import get_batch_run, list_batch_runs
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/run")
async def run_batch_now():
    return run_batch()


@router.get("/history")
async def batch_history():
    return {"batches": list_batch_runs()}


@router.get("/{batch_id}")
async def batch_detail(batch_id: str):
    record = get_batch_run(batch_id)
    if not record:
        raise HTTPException(status_code=404, detail="Batch run not found")
    return record


@router.get("/{batch_id}/audit")
async def batch_audit(batch_id: str):
    return {"audit_trail": get_audit_trail(batch_id, entity_type="batch")}
