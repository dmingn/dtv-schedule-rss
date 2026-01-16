import asyncio

from app.utils.cache import async_ttl_cache


async def test_async_ttl_cache_hit_and_miss():
    # A simple class to test caching on an instance method
    class Counter:
        def __init__(self):
            self.call_count = 0

        @async_ttl_cache(maxsize=1, ttl=1)
        async def cached_method(self):
            self.call_count += 1
            return "result"

    instance = Counter()

    # First call, should execute and cache
    assert await instance.cached_method() == "result"
    assert instance.call_count == 1

    # Second call, should be a cache hit
    assert await instance.cached_method() == "result"
    assert instance.call_count == 1

    # Wait for the cache to expire
    await asyncio.sleep(1.1)

    # Third call, should be a cache miss and re-execute
    assert await instance.cached_method() == "result"
    assert instance.call_count == 2
