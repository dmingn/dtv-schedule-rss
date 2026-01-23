import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import tenacity
from tenacity import wait_fixed

from app.utils.http import fetch_json_with_retry, fetch_with_retry


@pytest.fixture
def mock_client():
    return AsyncMock(spec=httpx.AsyncClient)


async def test_fetch_with_retry_success(mock_client):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_client.get.return_value = mock_response

    response = await fetch_with_retry(mock_client, "http://example.com")

    assert response == mock_response
    mock_client.get.assert_called_once()


@pytest.mark.parametrize(
    "exception",
    [
        httpx.TimeoutException("timeout"),
        httpx.NetworkError("network error"),
        httpx.RemoteProtocolError("protocol error"),
    ],
)
async def test_fetch_with_retry_retries_on_exception(mock_client, exception):
    mock_client.get.side_effect = [
        exception,
        MagicMock(spec=httpx.Response, status_code=200),
    ]

    await fetch_with_retry.retry_with(wait=wait_fixed(0))(
        mock_client, "http://example.com"
    )

    assert mock_client.get.call_count == 2


async def test_fetch_with_retry_logs_retry_attempt(mock_client, caplog):
    mock_client.get.side_effect = [
        httpx.TimeoutException("timeout"),
        MagicMock(spec=httpx.Response, status_code=200),
    ]

    with caplog.at_level("WARNING"):
        await fetch_with_retry.retry_with(wait=wait_fixed(0))(
            mock_client, "http://example.com"
        )

    assert len(caplog.records) == 1
    assert "HTTP fetch attempt 1 failed" in caplog.records[0].message
    assert "will retry" in caplog.records[0].message


async def test_fetch_with_retry_5xx_error(mock_client):
    mock_503_response = MagicMock(spec=httpx.Response, status_code=503)
    mock_client.get.side_effect = [
        mock_503_response,
        MagicMock(spec=httpx.Response, status_code=200),
    ]

    await fetch_with_retry.retry_with(wait=wait_fixed(0))(
        mock_client, "http://example.com"
    )

    assert mock_client.get.call_count == 2


async def test_fetch_with_retry_final_failure(mock_client):
    mock_client.get.side_effect = httpx.TimeoutException("timeout")

    with pytest.raises(tenacity.RetryError):
        await fetch_with_retry.retry_with(wait=wait_fixed(0))(
            mock_client, "http://example.com"
        )

    assert mock_client.get.call_count == 3


async def test_fetch_with_retry_logs_all_retry_attempts(mock_client, caplog):
    mock_client.get.side_effect = httpx.TimeoutException("timeout")

    with caplog.at_level("WARNING"):
        with pytest.raises(tenacity.RetryError):
            await fetch_with_retry.retry_with(wait=wait_fixed(0))(
                mock_client, "http://example.com"
            )

    assert len(caplog.records) == 2
    assert all("HTTP fetch attempt" in record.message for record in caplog.records)
    assert all("will retry" in record.message for record in caplog.records)


async def test_fetch_json_with_retry_success(mock_client):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_client.get.return_value = mock_response

    result = await fetch_json_with_retry(mock_client, "http://example.com")

    assert result == {"key": "value"}
    mock_client.get.assert_called_once()


async def test_fetch_json_with_retry_json_decode_error_retry(mock_client):
    mock_response_1 = MagicMock(spec=httpx.Response)
    mock_response_1.status_code = 200
    mock_response_1.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_response_1.headers = MagicMock()
    mock_response_1.headers.get.return_value = "application/json"
    mock_response_1.text = "invalid json"

    mock_response_2 = MagicMock(spec=httpx.Response)
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = {"key": "value"}

    mock_client.get.side_effect = [mock_response_1, mock_response_2]

    result = await fetch_json_with_retry.retry_with(wait=wait_fixed(0))(
        mock_client, "http://example.com"
    )

    assert result == {"key": "value"}
    assert mock_client.get.call_count == 2


async def test_fetch_json_with_retry_logs_json_decode_error(mock_client, caplog):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_response.headers = MagicMock()
    mock_response.headers.get.return_value = "application/json"
    mock_response.text = "invalid json"
    mock_client.get.return_value = mock_response

    with caplog.at_level("WARNING"):
        try:
            await fetch_json_with_retry.retry_with(wait=wait_fixed(0))(
                mock_client, "http://example.com"
            )
        except tenacity.RetryError:
            pass

    assert len(caplog.records) >= 1
    assert any("JSON decode error" in record.message for record in caplog.records)
    assert any(record.levelname == "WARNING" for record in caplog.records)


async def test_fetch_json_with_retry_json_decode_error_final_failure(mock_client):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_response.headers = MagicMock()
    mock_response.headers.get.return_value = "application/json"
    mock_response.text = "invalid json"
    mock_client.get.return_value = mock_response

    with pytest.raises(tenacity.RetryError):
        await fetch_json_with_retry.retry_with(wait=wait_fixed(0))(
            mock_client, "http://example.com"
        )

    assert mock_client.get.call_count == 3


async def test_fetch_json_with_retry_logs_all_retry_attempts(mock_client, caplog):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_response.headers = MagicMock()
    mock_response.headers.get.return_value = "application/json"
    mock_response.text = "invalid json"
    mock_client.get.return_value = mock_response

    with caplog.at_level("WARNING"):
        with pytest.raises(tenacity.RetryError):
            await fetch_json_with_retry.retry_with(wait=wait_fixed(0))(
                mock_client, "http://example.com"
            )

    # We expect 3 JSON decode error logs and 2 retry logs.
    assert len(caplog.records) == 5
    assert any("JSON decode error" in record.message for record in caplog.records)
    assert any(
        "JSON fetch/parse attempt" in record.message for record in caplog.records
    )
