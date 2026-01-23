from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.channels.tbs import fetch_programs


@pytest.mark.parametrize(
    "invalid_html, expected_exception",
    [
        # HTML with td element but missing required elements (strong, a)
        # to trigger AttributeError
        (
            (
                '<html><body><table><tr><td class="not-empty">'
                "</td></tr></table></body></html>"
            ),
            AttributeError,
        ),
        # HTML with td element but invalid datetime format to trigger ValueError
        (
            (
                '<html><body><table><tr><td class="not-empty">'
                '<strong>Title</strong><a href="/test">Link</a>'
                '<span class="starttime">invalid-datetime</span>'
                "</td></tr></table></body></html>"
            ),
            ValueError,
        ),
    ],
)
async def test_fetch_programs_logs_html_parse_error(
    caplog, invalid_html, expected_exception
):
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    with patch("app.channels.tbs.fetch_text_with_retry", return_value=invalid_html):
        with caplog.at_level("ERROR"):
            with pytest.raises(expected_exception):
                await fetch_programs(mock_client, "http://example.com")

    assert len(caplog.records) >= 1
    assert any(
        "HTML parse error" in r.message and r.levelname == "ERROR"
        for r in caplog.records
    )
    assert any("html_preview" in r.message for r in caplog.records)
