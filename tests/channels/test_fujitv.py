import datetime
from zoneinfo import ZoneInfo

import pytest

from app.channels.fujitv import parse_datetime


@pytest.mark.parametrize(
    "datetime_str, expected_datetime",
    [
        (
            "2025-03-20T00:00:00W1",
            datetime.datetime(2025, 3, 20, 0, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
        (
            "2025-03-20T12:34:56W1",
            datetime.datetime(2025, 3, 20, 12, 34, 56, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
        (
            "2025-03-20T24:34:56W1",
            datetime.datetime(2025, 3, 21, 0, 34, 56, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
    ],
)
def test_parse_datetime(datetime_str, expected_datetime):
    assert parse_datetime(datetime_str) == expected_datetime
