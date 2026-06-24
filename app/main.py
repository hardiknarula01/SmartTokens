from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.router import router
from app.db import init_db
from app.stats import get_stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="SmartToken",
    description="AI Token Optimization Proxy",
    version="0.2.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.2.0"}

@app.get("/stats")
def stats():
    return get_stats()