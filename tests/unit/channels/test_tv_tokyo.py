import datetime
from zoneinfo import ZoneInfo

import pytest

from app.channels.tv_tokyo import calc_start_from_date_hours_and_minutes


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
            24,
            00,
            datetime.datetime(2021, 1, 2, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo")),
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
