from app.api.routes.recovery import router as recovery_router
from app.api.routes.webhooks import router as webhook_router
from fastapi import FastAPI

app = FastAPI(
    title="Revive",
    description="Agentic Revenue Recovery Platform",
    version="1.0.0",
)

app.include_router(
    webhook_router,
    prefix="/webhooks",
    tags=["Webhooks"],
)

app.include_router(
    recovery_router,
    prefix="/recovery",
    tags=["Recovery"],
)


@app.get("/")
async def root():
    return {
        "name": "Revive",
        "description": "Agentic Revenue Recovery Platform",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
    }

