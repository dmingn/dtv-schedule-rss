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

    ET.fromstring(response.text)  # parse the XML to check if it's valid
