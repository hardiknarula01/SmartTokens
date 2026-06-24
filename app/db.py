# import asyncpg
# import os
# from dotenv import load_dotenv

# load_dotenv()

# CREATE_TABLE_SQL = """
# CREATE TABLE IF NOT EXISTS token_events (
#     id SERIAL PRIMARY KEY,
#     tokens_in INTEGER NOT NULL,
#     tokens_sent INTEGER NOT NULL,
#     tokens_out INTEGER NOT NULL,
#     tokens_saved INTEGER GENERATED ALWAYS AS (tokens_in - tokens_sent) STORED,
#     model VARCHAR(64),
#     created_at TIMESTAMPTZ DEFAULT NOW()
# );
# """

# async def get_connection():
#     return await asyncpg.connect(os.getenv("DATABASE_URL"))

# async def init_db():
#     conn = await get_connection()
#     await conn.execute(CREATE_TABLE_SQL)
#     await conn.close()
#     print("Database table ready.")

# async def log_event(tokens_in: int, tokens_sent: int, tokens_out: int, model: str):
#     try:
#         conn = await get_connection()
#         await conn.execute(
#             """
#             INSERT INTO token_events (tokens_in, tokens_sent, tokens_out, model)
#             VALUES ($1, $2, $3, $4)
#             """,
#             tokens_in, tokens_sent, tokens_out, model
#         )
#         await conn.close()
#     except Exception as e:
#         print(f"DB log failed (non-critical): {e}")

import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS token_events (
    id SERIAL PRIMARY KEY,
    tokens_in INTEGER NOT NULL,
    tokens_sent INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    tokens_saved INTEGER GENERATED ALWAYS AS (tokens_in - tokens_sent) STORED,
    model VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

async def get_connection():
    return await asyncpg.connect(os.getenv("DATABASE_URL"))

async def init_db():
    try:
        conn = await get_connection()
        await conn.execute(CREATE_TABLE_SQL)
        await conn.close()
        print("✅ Database ready.")
    except Exception as e:
        print(f"⚠️  Database skipped (will connect later): {e}")
        print("👉 Server will still work — database is optional for now.")

async def log_event(tokens_in: int, tokens_sent: int, tokens_out: int, model: str):
    try:
        conn = await get_connection()
        await conn.execute(
            "INSERT INTO token_events (tokens_in, tokens_sent, tokens_out, model) VALUES ($1, $2, $3, $4)",
            tokens_in, tokens_sent, tokens_out, model
        )
        await conn.close()
    except Exception:
        pass  # silently skip if db not connected