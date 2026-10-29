from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.utils.http import create_http_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Manages the application's lifespan, including the HTTP client.
    """
    async with create_http_client() as client:
        app.state.http_client = client
        yield
