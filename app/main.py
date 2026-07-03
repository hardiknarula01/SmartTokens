from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.router import router
from app.db import init_db, get_all_stats
from app.stats import get_stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup — connects to database
    await init_db()
    yield
    # Runs once at shutdown — nothing needed here yet

app = FastAPI(
    title="SmartToken",
    description="AI Token Optimization Proxy",
    version="0.3.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0"}

@app.get("/stats")
async def stats():
    # Try database first — permanent data
    db_stats = await get_all_stats()

    if db_stats:
        # Database is connected — use real permanent stats
        total_in  = db_stats["total_tokens_in"]
        total_saved = db_stats["total_tokens_saved"]
        avg = round((total_saved / total_in * 100), 1) if total_in > 0 else 0
        return {
            "source":             "database",
            "total_requests":     int(db_stats["total_requests"]),
            "total_tokens_in":    int(db_stats["total_tokens_in"]),
            "total_tokens_sent":  int(db_stats["total_tokens_sent"]),
            "total_tokens_saved": int(db_stats["total_tokens_saved"]),
            "total_tokens_out":   int(db_stats["total_tokens_out"]),
            "avg_reduction_pct":  f"{avg}%"
        }
    else:
        # Database not connected — fall back to in-memory stats
        result = get_stats()
        result["source"] = "memory"
        return result