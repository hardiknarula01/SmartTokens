import pytest
import app.cache as cache_module
from app.cache import get_cached, set_cached, make_cache_key

def test_cache_key_is_consistent():
    """Same prompt and model always produce the same key"""
    key1 = make_cache_key("What is Python?", "llama-3.3")
    key2 = make_cache_key("What is Python?", "llama-3.3")
    assert key1 == key2

def test_cache_key_differs_for_different_prompts():
    """Different prompts produce different keys"""
    key1 = make_cache_key("What is Python?", "llama-3.3")
    key2 = make_cache_key("What is JavaScript?", "llama-3.3")
    assert key1 != key2

def test_cache_key_differs_for_different_models():
    """Same prompt but different model produces different key"""
    key1 = make_cache_key("What is Python?", "llama-3.3")
    key2 = make_cache_key("What is Python?", "gpt-4o")
    assert key1 != key2

def test_cache_key_starts_with_prefix():
    """Cache key has smarttoken prefix for namespacing"""
    key = make_cache_key("test", "model")
    assert key.startswith("smarttoken:cache:")

@pytest.mark.asyncio
async def test_get_cached_returns_none_when_no_redis():
    """When Redis is not connected get_cached returns None"""
    original = cache_module._redis
    cache_module._redis = None
    try:
        result = await get_cached("What is Python?", "llama-3.3")
        assert result is None
    finally:
        cache_module._redis = original

@pytest.mark.asyncio
async def test_set_cached_returns_false_when_no_redis():
    """When Redis is not connected set_cached returns False"""
    original = cache_module._redis
    cache_module._redis = None
    try:
        result = await set_cached("What is Python?", "llama-3.3", {"test": "data"})
        assert result is False
    finally:
        cache_module._redis = original