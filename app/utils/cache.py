from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from cachetools import TTLCache


def async_ttl_cache(maxsize: int = 128, ttl: int = 300) -> Callable:
    """
    A simple async-aware TTL cache decorator.
    """
    cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(fn: Callable[..., Coroutine]) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Note: This simple key generation might not be robust for all cases,
            # but it's sufficient for this project's needs.
            key = str(args) + str(kwargs)
            try:
                return cache[key]
            except KeyError:
                pass  # Cache miss

            val = await fn(*args, **kwargs)
            cache[key] = val
            return val

        return wrapper

    return decorator
