import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class Http5xxError(Exception):
    """Custom exception for HTTP 5xx errors."""

    def __init__(self, response: httpx.Response):
        self.response = response
        super().__init__(f"Server error: {response.status_code} for url {response.url}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(
        (httpx.TimeoutException, httpx.NetworkError, Http5xxError)
    ),
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """
    Fetches a URL with retries on transient errors.
    """
    response = await client.get(url)
    if 500 <= response.status_code < 600:
        raise Http5xxError(response)
    response.raise_for_status()
    return response
