from datetime import date

from app.models.receivable import Receivable
from app.services.audit import get_audit_trail
from app.services.receivables_repository import list_receivables
from app.services.receivables_service import (
    chase_batch,
    chase_single,
    create_receivable,
    mark_receivable_paid,
    record_promise_to_pay,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


@router.get("")
async def get_receivables(status: str | None = None):
    return {"receivables": list_receivables(status=status)}


@router.post("")
async def add_receivable(receivable: Receivable):
    return create_receivable(receivable)


class PromiseIn(BaseModel):
    promise_to_pay_date: date
    amount: int = Field(gt=0)


@router.post("/{invoice_id}/promise")
async def promise_to_pay(invoice_id: str, payload: PromiseIn):
    result = record_promise_to_pay(invoice_id, payload.promise_to_pay_date, payload.amount)
    if not result:
        raise HTTPException(status_code=404, detail="Receivable not found")
    return result


class PaidIn(BaseModel):
    recovered_amount: int = Field(gt=0)


@router.post("/{invoice_id}/mark-paid")
async def mark_paid(invoice_id: str, payload: PaidIn):
    result = mark_receivable_paid(invoice_id, payload.recovered_amount)
    if not result:
        raise HTTPException(status_code=404, detail="Receivable not found")
    return result


@router.post("/{invoice_id}/chase")
async def chase_one(invoice_id: str):
    result = chase_single(invoice_id)
    if not result:
        raise HTTPException(status_code=404, detail="Receivable not found")
    return result


@router.post("/batch/chase")
async def chase_all():
    """Run the compliant escalation ladder across every open receivable and
    return a measured summary: how many were contacted, escalated to a human,
    or stopped by a stopping rule."""
    return chase_batch()


@router.get("/{invoice_id}/audit")
async def receivable_audit(invoice_id: str):
    return {"audit_trail": get_audit_trail(invoice_id, entity_type="receivable")}
