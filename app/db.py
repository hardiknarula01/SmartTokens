import asyncpg
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Global connection pool — created once at startup, reused for every request
# None until init_db() is called
_pool = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS token_events (
    id            SERIAL PRIMARY KEY,
    tokens_in     INTEGER NOT NULL,
    tokens_sent   INTEGER NOT NULL,
    tokens_out    INTEGER NOT NULL,
    tokens_saved  INTEGER GENERATED ALWAYS AS (tokens_in - tokens_sent) STORED,
    model         VARCHAR(64),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
"""

async def init_db():
    """
    Called once when server starts.
    Creates the connection pool and the token_events table.
    Concept: SERIAL = auto-incrementing integer ID (PostgreSQL)
    Concept: TIMESTAMPTZ = timestamp with timezone (always store UTC)
    Concept: GENERATED ALWAYS AS = computed column, PostgreSQL calculates it automatically
    """
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=2,   # keep 2 connections open always
            max_size=10   # open up to 10 connections under load
        )
        # Create table if it does not exist yet
        async with _pool.acquire() as conn:
            await conn.execute(CREATE_TABLE_SQL)
        print("✅ Database connected and table ready.")
    except Exception as e:
        print(f"⚠️  Database skipped (will connect later): {e}")
        print("👉 Server will still work without database.")
        _pool = None

async def log_event(tokens_in: int, tokens_sent: int, tokens_out: int, model: str):
    """
    Called after every request to save the token event permanently.
    Concept: if not _pool — safely skips if database is not connected
    Concept: pool.acquire() — borrows a connection, returns it when done
    """
    if not _pool:
        return  # silently skip if database not connected

    try:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO token_events
                    (tokens_in, tokens_sent, tokens_out, model)
                VALUES
                    ($1, $2, $3, $4)
                """,
                tokens_in, tokens_sent, tokens_out, model
            )
    except Exception as e:
        print(f"DB log skipped: {e}")

async def get_all_stats():
    """
    NEW — reads total savings from PostgreSQL.
    Concept: SUM() — adds up all values in a column across all rows
    Concept: COUNT(*) — counts total number of rows
    Concept: COALESCE — returns 0 instead of NULL when table is empty
    """
    if not _pool:
        return None

    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*)                        AS total_requests,
                    COALESCE(SUM(tokens_in), 0)     AS total_tokens_in,
                    COALESCE(SUM(tokens_sent), 0)   AS total_tokens_sent,
                    COALESCE(SUM(tokens_saved), 0)  AS total_tokens_saved,
                    COALESCE(SUM(tokens_out), 0)    AS total_tokens_out,
                    COALESCE(AVG(
                        CASE WHEN tokens_in > 0
                        THEN (tokens_in - tokens_sent)::float / tokens_in * 100
                        ELSE 0 END
                    ), 0)                           AS avg_reduction_pct
                FROM token_events
                """
            )
            return dict(row)
    except Exception as e:
        print(f"DB stats query failed: {e}")
        return None