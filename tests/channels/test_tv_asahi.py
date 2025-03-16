import datetime
from zoneinfo import ZoneInfo

import pytest
from bs4 import BeautifulSoup

from app.channels.tv_asahi import calc_start_from_date_hours_and_minutes, parse_day_str


@pytest.mark.parametrize(
    "day_str, expected",
    [
        (
            "1月1日(月)",
            datetime.datetime(
                year=datetime.datetime.now().year,
                month=1,
                day=1,
                tzinfo=ZoneInfo("Asia/Tokyo"),
            ),
        ),
        (
            "12月31日(火)",
            datetime.datetime(
                year=datetime.datetime.now().year,
                month=12,
                day=31,
                tzinfo=ZoneInfo("Asia/Tokyo"),
            ),
        ),
    ],
)
def test_parse_day_str(day_str: str, expected: datetime.datetime):
    assert parse_day_str(day_str) == expected


@pytest.mark.parametrize(
    "date, hours, minutes, expected",
    [
        (
            datetime.datetime(2021, 1, 1, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
            4,
            0,
            datetime.datetime(2021, 1, 1, 4, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
        (
            datetime.datetime(2021, 1, 1, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
            23,
            59,
            datetime.datetime(2021, 1, 1, 23, 59, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
        (
            datetime.datetime(2021, 1, 1, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
            0,
            0,
            datetime.datetime(2021, 1, 2, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
        (
            datetime.datetime(2021, 1, 1, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
            3,
            59,
            datetime.datetime(2021, 1, 2, 3, 59, tzinfo=ZoneInfo("Asia/Tokyo")),
        ),
    ],
)
def test_calc_start_from_date_hours_and_minutes(date, hours, minutes, expected):
    assert calc_start_from_date_hours_and_minutes(date, hours, minutes) == expected
