import datetime
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.channels.tv_asahi import (
    calc_start_from_date_hours_and_minutes,
    fetch_programs,
    parse_day_str,
)


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


@pytest.mark.parametrize(
    "invalid_html, expected_exception",
    [
        # HTML without ttDay element to trigger ValueError
        (
            "<html><body>No ttDay element</body></html>",
            ValueError,
        ),
        # HTML with ttDay and 7 dates/bangumi_list_tds but missing prog_name_span
        # to trigger AttributeError in parse_new_day_table
        (
            '<html><body><table><tr id="ttDay">'
            '<td class="not-none">1月1日(月)</td>'
            '<td class="not-none">1月2日(火)</td>'
            '<td class="not-none">1月3日(水)</td>'
            '<td class="not-none">1月4日(木)</td>'
            '<td class="not-none">1月5日(金)</td>'
            '<td class="not-none">1月6日(土)</td>'
            '<td class="not-none">1月7日(日)</td></tr></table>'
            '<td valign="top"><table class="new_day">'
            '<span class="min">12:00</span>'
            "</table></td>"
            '<td valign="top"></td><td valign="top"></td>'
            '<td valign="top"></td><td valign="top"></td>'
            '<td valign="top"></td><td valign="top"></td></body></html>',
            AttributeError,
        ),
    ],
)
async def test_fetch_programs_logs_html_parse_error(
    caplog, invalid_html, expected_exception
):
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    with patch(
        "app.channels.tv_asahi.fetch_text_with_retry", return_value=invalid_html
    ):
        with caplog.at_level("ERROR"):
            with pytest.raises(expected_exception):
                await fetch_programs(mock_client, "http://example.com")

    assert len(caplog.records) >= 1
    assert any(
        "HTML parse error" in r.message and r.levelname == "ERROR"
        for r in caplog.records
    )
    assert any("html_preview" in r.message for r in caplog.records)
