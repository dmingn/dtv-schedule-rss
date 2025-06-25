import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from app.main import app, path_to_channel

client = TestClient(app)


def test_get_schedule_rss_returns_404_for_unknown_path():
    response = client.get("/unknown")
    assert response.status_code == 404


@pytest.mark.parametrize("path", path_to_channel.keys())
def test_get_schedule_rss_returns_xml(path: str):
    response = client.get(f"/{path}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"

    root = ET.fromstring(response.text)  # parse the XML to check if it's valid
    assert root.tag == "rss"

    channel = root.find("channel")
    assert channel is not None
    assert channel.findtext("title") is not None and channel.findtext("title").strip() != ""
    assert channel.findtext("link") is not None and channel.findtext("link").strip() != ""
    assert channel.findtext("description") is not None  # Allow empty description

    # Check if there's at least one item and verify its content
    items = channel.findall("item")
    assert items is not None and len(items) > 0  # Ensure there is at least one item

    for item in items:
        assert item.findtext("title") is not None and item.findtext("title").strip() != ""
        # Allow item link to be missing or empty
        item_link = item.findtext("link")
        assert item_link is not None or item.find("link") is None or item_link.strip() == ""
        assert item.findtext("description") is not None and item.findtext("description").strip() != ""
        assert item.findtext("pubDate") is not None and item.findtext("pubDate").strip() != ""
