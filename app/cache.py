import redis.asyncio as aioredis
import hashlib
import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# ── Global Redis connection ───────────────────────────────────────────────────
# None until init_cache() is called at startup
_redis = None

# How long to keep cached results (in seconds)
# 3600 = 1 hour
CACHE_TTL = 3600

async def init_cache():
    """
    Called once at startup.
    Creates the Redis connection.

    Concept: redis.asyncio
    This is the async version of the Redis client.
    Works with FastAPI's async system just like asyncpg does for PostgreSQL.

    Concept: decode_responses=True
    Redis stores bytes by default.
    This setting automatically converts bytes to strings so you get
    normal Python strings back instead of b"string" byte objects.
    """
    global _redis
    try:
        _redis = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )
        # Test the connection with a ping
        await _redis.ping()
        print("✅ Redis cache connected.")
    except Exception as e:
        print(f"⚠️  Redis skipped: {e}")
        print("👉 Server works without cache — requests go directly to Groq.")
        _redis = None

def make_cache_key(prompt: str, model: str) -> str:
    """
    Creates a unique short key for a prompt + model combination.

    Concept: SHA-256 hashing
    hashlib.sha256() takes any text and produces a fixed 64-character string.
    "What is Python?" + "llama-3.3" → "a3f8b2c1d4e5..."
    Even one character difference produces a completely different hash.
    This is how we create unique short keys for long prompts.

    Concept: encode()
    hashlib needs bytes not strings.
    .encode() converts a Python string to bytes.
    .hexdigest() converts the hash result to a readable hex string.
    """
    combined = f"{model}:{prompt}"
    return f"smarttoken:cache:{hashlib.sha256(combined.encode()).hexdigest()}"

async def get_cached(prompt: str, model: str):
    """
    Check if a result exists in cache for this prompt + model.
    Returns the cached result dict if found, or None if not found.

    Concept: cache hit vs cache miss
    Cache hit  = key exists in Redis → return stored result instantly
    Cache miss = key not in Redis   → must call Groq API
    """
    if not _redis:
        return None  # no cache available

    try:
        key = make_cache_key(prompt, model)
        # _redis.get() returns the stored string or None if key does not exist
        cached = await _redis.get(key)

        if cached:
            # Convert JSON string back to Python dictionary
            return json.loads(cached)
        return None
    except Exception as e:
        print(f"Cache get failed (non-critical): {e}")
        return None

async def set_cached(prompt: str, model: str, result: dict) -> bool:
    """
    Store a result in cache for this prompt + model.
    Returns True if stored successfully, False if failed.

    Concept: ex=CACHE_TTL
    ex stands for expiry in seconds.
    Redis automatically deletes this key after CACHE_TTL seconds.
    No manual cleanup needed.
    """
    if not _redis:
        return False

    try:
        key = make_cache_key(prompt, model)
        # Convert Python dictionary to JSON string for storage
        await _redis.set(key, json.dumps(result), ex=CACHE_TTL)
        return True
    except Exception as e:
        print(f"Cache set failed (non-critical): {e}")
        return False

async def get_cache_stats() -> dict:
    """
    Returns basic stats about the cache.

    Concept: Redis INFO command
    Redis has a built-in INFO command that returns server statistics.
    keyspace_hits = number of successful cache lookups
    keyspace_misses = number of failed cache lookups
    These are tracked automatically by Redis.
    """
    if not _redis:
        return {"connected": False}

    try:
        info = await _redis.info("stats")
        total_hits   = info.get("keyspace_hits", 0)
        total_misses = info.get("keyspace_misses", 0)
        total         = total_hits + total_misses
        hit_rate = round((total_hits / total * 100), 1) if total > 0 else 0

        return {
            "connected":    True,
            "total_hits":   total_hits,
            "total_misses": total_misses,
            "hit_rate_pct": f"{hit_rate}%",
            "ttl_seconds":  CACHE_TTL
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}