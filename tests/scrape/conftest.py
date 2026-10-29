from collections.abc import AsyncIterator

import httpx
import pytest


@pytest.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    timeout = httpx.Timeout(10.0, connect=5.0, read=30.0)
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
    async with httpx.AsyncClient(timeout=timeout, limits=limits, http2=True) as client:
        yield client
