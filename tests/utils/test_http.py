from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import tenacity

from app.utils.http import fetch_with_retry


@pytest.fixture
def mock_client():
    return AsyncMock(spec=httpx.AsyncClient)


async def test_fetch_with_retry_success(mock_client):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_client.get.return_value = mock_response

    response = await fetch_with_retry(mock_client, "http://test.com")

    assert response == mock_response
    mock_client.get.assert_called_once()


async def test_fetch_with_retry_timeout(mock_client):
    mock_client.get.side_effect = [
        httpx.TimeoutException("timeout"),
        MagicMock(spec=httpx.Response, status_code=200),
    ]

    await fetch_with_retry(mock_client, "http://test.com")

    assert mock_client.get.call_count == 2


async def test_fetch_with_retry_network_error(mock_client):
    mock_client.get.side_effect = [
        httpx.NetworkError("network error"),
        MagicMock(spec=httpx.Response, status_code=200),
    ]

    await fetch_with_retry(mock_client, "http://test.com")

    assert mock_client.get.call_count == 2


async def test_fetch_with_retry_5xx_error(mock_client):
    mock_503_response = MagicMock(spec=httpx.Response, status_code=503)
    mock_client.get.side_effect = [
        mock_503_response,
        MagicMock(spec=httpx.Response, status_code=200),
    ]

    await fetch_with_retry(mock_client, "http://test.com")

    assert mock_client.get.call_count == 2


async def test_fetch_with_retry_final_failure(mock_client):
    mock_client.get.side_effect = httpx.TimeoutException("timeout")

    with pytest.raises(tenacity.RetryError):
        await fetch_with_retry(mock_client, "http://test.com")

    assert mock_client.get.call_count == 3
