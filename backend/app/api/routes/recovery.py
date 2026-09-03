from app.services.mongodb import (
    payments_collection,
    recoveries_collection,
)
from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def recovery_summary():
    total_failed = await payments_collection.count_documents({"status": "failed"})

    recoverable = await recoveries_collection.count_documents(
        {"execution_success": True}
    )

    recovered_cursor = await recoveries_collection.aggregate(
        [
            {
                "$match": {
                    "execution_success": True,
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {
                        "$sum": "$recovered_amount",
                    },
                }
            },
        ]
    )
    recovered = await recovered_cursor.to_list(length=1)

    recovered_amount = recovered[0]["total"] if recovered else 0

    recovery_rate = (recoverable / total_failed) * 100 if total_failed else 0

    return {
        "total_failed_payments": total_failed,
        "recoverable_payments": recoverable,
        "recovered_amount": recovered_amount,
        "recovery_rate": round(
            recovery_rate,
            2,
        ),
    }


@router.get("/payments")
async def recovery_payments():
    payments = (
        await payments_collection.find(
            {},
            {
                "_id": 0,
            },
        )
        .sort(
            "created_at",
            -1,
        )
        .to_list(length=100)
    )

    return {
        "payments": payments,
    }


@router.get("/recoveries")
async def recovery_history():
    recoveries = (
        await recoveries_collection.find(
            {},
            {
                "_id": 0,
            },
        )
        .sort(
            "created_at",
            -1,
        )
        .to_list(length=100)
    )

    return {
        "recoveries": recoveries,
    }
