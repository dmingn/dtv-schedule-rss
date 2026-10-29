from collections.abc import AsyncIterator

import httpx
import pytest

from app.utils.http import create_http_client


@pytest.fixture
async def http_client() -> AsyncIterator[httpx.AsyncClient]:
    async with create_http_client() as client:
        yield client
