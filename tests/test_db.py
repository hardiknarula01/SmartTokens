import pytest
from app.db import log_event, get_all_stats
import app.db as db_module

# Concept: pytest.mark.asyncio — tells pytest this test is async
# Concept: monkeypatching — temporarily replacing _pool with None to simulate no DB

@pytest.mark.asyncio
async def test_log_event_skips_when_no_pool():
    """When database is not connected, log_event should silently skip"""
    original_pool = db_module._pool
    db_module._pool = None  # simulate no database connection
    try:
        # Should not raise any exception — just silently skip
        await log_event(100, 80, 50, "test-model")
    finally:
        db_module._pool = original_pool  # restore original

@pytest.mark.asyncio
async def test_get_all_stats_returns_none_when_no_pool():
    """When database is not connected, get_all_stats should return None"""
    original_pool = db_module._pool
    db_module._pool = None
    try:
        result = await get_all_stats()
        assert result is None
    finally:
        db_module._pool = original_pool