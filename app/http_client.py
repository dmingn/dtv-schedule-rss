from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI


class AppState:
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manages the application's lifespan, including the HTTP client.
    """
    timeout = httpx.Timeout(10.0, connect=5.0, read=30.0)
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, http2=True) as client:
        app.state.http_client = client
        yield
