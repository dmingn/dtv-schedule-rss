import asyncio

from app.utils.cache import async_ttl_cache


async def test_async_ttl_cache_hit_and_miss():
    # A simple async function to cache
    call_count = 0

    @async_ttl_cache(maxsize=1, ttl=1)
    async def cached_function():
        nonlocal call_count
        call_count += 1
        return "result"

    # First call, should execute and cache
    assert await cached_function() == "result"
    assert call_count == 1

    # Second call, should be a cache hit
    assert await cached_function() == "result"
    assert call_count == 1

    # Wait for the cache to expire
    await asyncio.sleep(1.1)

    # Third call, should be a cache miss and re-execute
    assert await cached_function() == "result"
    assert call_count == 2
