import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_exception

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

class Http5xxError(Exception):
    """Custom exception for HTTP 5xx errors."""
    def __init__(self, response: httpx.Response):
        self.response = response
        super().__init__(f"Server error: {response.status_code} for url {response.url}")

def is_http_5xx_error(exception: BaseException) -> bool:
    """Return True if the exception is an HTTP 5xx error."""
    return (
        isinstance(exception, Http5xxError) and
        500 <= exception.response.status_code < 600
    )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)) | retry_if_exception(is_http_5xx_error),
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """
    Fetches a URL with retries on transient errors.
    """
    response = await client.get(url, timeout=DEFAULT_TIMEOUT)
    if 500 <= response.status_code < 600:
        raise Http5xxError(response)
    response.raise_for_status()
    return response
