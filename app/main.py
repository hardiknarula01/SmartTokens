from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.router import router
from app.db import init_db, get_all_stats
from app.stats import get_stats
from app.cache import init_cache, get_cache_stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()     # connect PostgreSQL
    await init_cache()  # connect Redis
    yield

app = FastAPI(
    title="SmartToken",
    description="AI Token Optimization Proxy",
    version="0.4.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.4.0"}

@app.get("/stats")
async def stats():
    db_stats    = await get_all_stats()
    cache_stats = await get_cache_stats()

    if db_stats:
        total_in    = int(db_stats["total_tokens_in"])
        total_saved = int(db_stats["total_tokens_saved"])
        avg = round((total_saved / total_in * 100), 1) if total_in > 0 else 0
        return {
            "source":             "database",
            "total_requests":     int(db_stats["total_requests"]),
            "total_tokens_in":    total_in,
            "total_tokens_sent":  int(db_stats["total_tokens_sent"]),
            "total_tokens_saved": total_saved,
            "total_tokens_out":   int(db_stats["total_tokens_out"]),
            "avg_reduction_pct":  f"{avg}%",
            "cache":              cache_stats
        }
    else:
        result = get_stats()
        result["source"] = "memory"
        result["cache"]  = cache_stats
        return result

@app.get("/cache/stats")
async def cache_stats():
    return await get_cache_stats()