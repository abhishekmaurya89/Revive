from app.services.audit import get_audit_trail, list_recent_audit_events
from app.services.batch import run_batch
from app.services.batch_repository import get_batch_run, list_batch_runs
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class BatchRunInput(BaseModel):
    portfolio_size: int = Field(default=42, ge=20, le=100)


@router.post("/run")
async def run_batch_now(payload: BatchRunInput | None = None):
    return run_batch(payload.portfolio_size if payload else 42)


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
