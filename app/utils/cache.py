from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from cachetools import TTLCache


def async_ttl_cache(maxsize: int = 128, ttl: int = 300) -> Callable:
    """
    A simple async-aware TTL cache decorator.
    """
    cache: TTLCache[int, Any] = TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(fn: Callable[..., Coroutine]) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a cache key from args and kwargs
            # Convert kwargs dict to sorted tuple (dict is unhashable),
            # then use hash() to get an integer key for the cache
            key = hash((args, tuple(sorted(kwargs.items()))))
            try:
                return cache[key]
            except KeyError:
                pass  # Cache miss

            val = await fn(*args, **kwargs)
            cache[key] = val
            return val

        return wrapper

    return decorator
