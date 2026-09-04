from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import client

from app.api.routes.audit import router as audit_router
from app.api.routes.batch import router as batch_router
from app.api.routes.events import router as events_router
from app.api.routes.receivables import router as receivables_router
from app.api.routes.recovery import router as recovery_router
from app.api.routes.webhooks import router as webhook_router


app = FastAPI(
    title="Revive",
    description="Agentic Revenue Recovery Platform",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(events_router, prefix="/events", tags=["Events"])
app.include_router(recovery_router, prefix="/recovery", tags=["Recovery"])
app.include_router(receivables_router, prefix="/receivables", tags=["Receivables"])
app.include_router(batch_router, prefix="/batch", tags=["Batch"])
app.include_router(audit_router, prefix="/audit", tags=["Audit"])


@app.get("/")
async def root():
    return {
        "name": "Revive",
        "description": "Agentic Revenue Recovery Platform",
        "status": "running",
    }


@app.get("/health")
async def health():
    try:
        client.admin.command("ping")
        return {"status": "healthy", "mongodb": "connected"}
    except Exception:
        return {"status": "degraded", "mongodb": "unavailable"}
