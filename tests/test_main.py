import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.channel import Schedule
from app.main import app, path_to_channel

def test_get_schedule_rss_returns_404_for_unknown_path():
    with TestClient(app) as client:
        response = client.get("/unknown")
        assert response.status_code == 404


@pytest.mark.parametrize("path", path_to_channel.keys())
def test_get_schedule_rss_returns_xml(path: str):
    channel_instance = path_to_channel[path]
    with patch.object(
        channel_instance,
        "fetch_schedule",
        new=AsyncMock(
            return_value=Schedule(
                channel_name="Test Channel",
                channel_url="http://test.com",
                programs=[],
            )
        ),
    ), TestClient(app) as client:
        response = client.get(f"/{path}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xml"

        ET.fromstring(response.text)  # parse the XML to check if it's valid
