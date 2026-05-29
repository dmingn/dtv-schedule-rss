import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from app.channel import Schedule
from app.main import app, path_to_channel


def test_get_schedule_rss_returns_404_for_unknown_path():
    with TestClient(app) as client:
        response = client.get("/unknown")
        assert response.status_code == 404


def test_get_top_page_returns_html():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<title>テレビ番組表 RSS フィード</title>" in response.text
        for path, channel in path_to_channel.items():
            assert f'href="http://testserver/{path}"' in response.text
            assert f">{channel.channel_name}</a>" in response.text


def test_get_top_page_with_root_path_returns_html():
    with TestClient(app, root_path="/dtv-rss") as client:
        response = client.get("/")
        assert response.status_code == 200
        for path, channel in path_to_channel.items():
            assert f'href="http://testserver/dtv-rss/{path}"' in response.text


@pytest.mark.parametrize("path", path_to_channel.keys())
def test_get_schedule_rss_returns_xml(path: str):
    channel_instance = path_to_channel[path]
    with (
        patch.object(
            channel_instance,
            "fetch_schedule",
            new=AsyncMock(
                return_value=Schedule(
                    channel_name="Test Channel",
                    channel_url=HttpUrl("http://example.com"),
                    programs=[],
                )
            ),
        ),
        TestClient(app) as client,
    ):
        response = client.get(f"/{path}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"

        ET.fromstring(response.text)  # parse the XML to check if it's valid


@pytest.mark.parametrize("path", path_to_channel.keys())
def test_get_schedule_rss_logs_error_on_exception(path: str, caplog):
    channel_instance = path_to_channel[path]
    with (
        patch.object(
            channel_instance,
            "fetch_schedule",
            new=AsyncMock(side_effect=Exception("Test error")),
        ),
        TestClient(app) as client,
    ):
        with caplog.at_level("ERROR"):
            response = client.get(f"/{path}")

    assert response.status_code == 500
    assert len(caplog.records) >= 1
    assert any(
        f"Error fetching schedule for path: {path}" in r.message
        and r.levelname == "ERROR"
        for r in caplog.records
    )
