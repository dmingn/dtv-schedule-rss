import json
import logging
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class Http5xxError(Exception):
    """Custom exception for HTTP 5xx errors."""

    def __init__(self, response: httpx.Response):
        self.response = response
        super().__init__(f"Server error: {response.status_code} for url {response.url}")


def _make_retry_attempt_logger(operation: str):
    """Create a retry attempt logger for the given operation."""

    def _log_retry_attempt(retry_state: RetryCallState) -> None:
        attempt = retry_state.attempt_number
        exception = retry_state.outcome.exception() if retry_state.outcome else None
        url = retry_state.kwargs.get("url", "unknown")
        if exception:
            logger.warning(
                f"{operation} attempt {attempt} failed for {url}: {exception}, "
                "will retry"
            )

    return _log_retry_attempt


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            Http5xxError,
        )
    ),
    before_sleep=_make_retry_attempt_logger("HTTP fetch"),
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """
    Fetches a URL with retries on transient errors.
    """
    logger.debug(f"Fetching URL: {url}")
    response = await client.get(url)
    if 500 <= response.status_code < 600:
        raise Http5xxError(response)
    response.raise_for_status()
    logger.debug(f"Successfully fetched URL: {url} (status: {response.status_code})")
    return response


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(json.JSONDecodeError),
    before_sleep=_make_retry_attempt_logger("JSON fetch/parse"),
)
async def fetch_json_with_retry(client: httpx.AsyncClient, url: str) -> Any:
    """
    Fetches a URL and parses JSON with retries on transient errors
    and JSON decode errors.
    """
    response = await fetch_with_retry(client, url)

    try:
        response_json = response.json()
    except json.JSONDecodeError:
        content_type = response.headers.get("Content-Type", "unknown")
        body_preview = response.text[:200] if response.text else "(empty)"
        logger.exception(
            f"JSON decode error for {url}: status={response.status_code}, "
            f"content_type={content_type}, body_preview={body_preview!r}"
        )
        raise

    logger.debug(f"Successfully parsed JSON from {url}")
    return response_json
