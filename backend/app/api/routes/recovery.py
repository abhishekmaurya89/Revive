from app.database import (
    payments_collection,
    receivables_collection,
    recoveries_collection,
)
from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def recovery_summary():
    total_failed = payments_collection.count_documents({"status": {"$in": ["failed", "abandoned"]}})
    payment_links_created = recoveries_collection.count_documents({"execution_success": True})
    successful_recoveries = recoveries_collection.count_documents({"status": "recovered"})
    stopped_count = recoveries_collection.count_documents({"stopped": True})
    escalated_or_approval = recoveries_collection.count_documents(
        {"$or": [{"requires_approval": True}, {"action": "escalate"}]}
    )

    payments_recovered_aggregate = list(
        recoveries_collection.aggregate(
            [
                {"$match": {"status": "recovered"}},
                {"$group": {"_id": None, "total": {"$sum": "$recovered_amount"}}},
            ]
        )
    )
    payments_recovered_amount = (
        payments_recovered_aggregate[0]["total"] if payments_recovered_aggregate else 0
    )

    total_receivables = receivables_collection.count_documents({})
    open_receivables = receivables_collection.count_documents(
        {"status": {"$nin": ["recovered"]}}
    )
    escalated_receivables = receivables_collection.count_documents({"status": "escalated"})
    at_risk_amount_aggregate = list(
        receivables_collection.aggregate(
            [
                {"$match": {"status": {"$nin": ["recovered"]}}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]
        )
    )
    receivables_at_risk_amount = (
        at_risk_amount_aggregate[0]["total"] if at_risk_amount_aggregate else 0
    )
    receivables_recovered_aggregate = list(
        receivables_collection.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$recovered_amount"}}}]
        )
    )
    receivables_recovered_amount = (
        receivables_recovered_aggregate[0]["total"] if receivables_recovered_aggregate else 0
    )

    total_recovered_amount = payments_recovered_amount + receivables_recovered_amount

    return {
        "payments": {
            "total_failed_or_abandoned": total_failed,
            "payment_links_created": payment_links_created,
            "successful_recoveries": successful_recoveries,
            "recovered_amount": payments_recovered_amount,
            "recovery_rate": round(
                (successful_recoveries / total_failed) * 100 if total_failed else 0, 2
            ),
            "stopped_by_policy": stopped_count,
            "escalated_or_pending_approval": escalated_or_approval,
        },
        "receivables": {
            "total": total_receivables,
            "open": open_receivables,
            "escalated": escalated_receivables,
            "at_risk_amount": receivables_at_risk_amount,
            "recovered_amount": receivables_recovered_amount,
        },
        "recovered_amount": total_recovered_amount,
    }


@router.get("/payments")
async def recovery_payments():
    payments = list(
        payments_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(100)
    )
    return {"payments": payments}


@router.get("/recoveries")
async def recovery_history():
    recoveries = list(
        recoveries_collection.find({}, {"_id": 0}).sort("created_at", -1).limit(100)
    )
    return {"recoveries": recoveries}
