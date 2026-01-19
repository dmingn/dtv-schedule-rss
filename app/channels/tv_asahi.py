import asyncio
import datetime
import itertools
import re
from zoneinfo import ZoneInfo

import httpx
from async_lru import alru_cache
from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from app.channel import Channel, Program, Schedule
from app.utils.http import fetch_with_retry


def parse_day_str(day_str: str) -> datetime.datetime:
    match = re.search(r"(\d+)月(\d+)日", day_str)

    if not match:
        raise ValueError(f"Invalid day string: {day_str}")

    month, day = match.groups()

    return datetime.datetime(
        year=datetime.datetime.now().year,  # FIXME
        month=int(month),
        day=int(day),
        tzinfo=ZoneInfo("Asia/Tokyo"),
    )


def calc_start_from_date_hours_and_minutes(
    date: datetime.datetime, hours: int, minutes: int
) -> datetime.datetime:
    return date + datetime.timedelta(
        days=1 if hours < 4 else 0, hours=hours, minutes=minutes
    )


def parse_new_day_table(new_day_table, date: datetime.datetime) -> Program:
    min_span = new_day_table.find("span", class_="min")
    prog_name_span = new_day_table.find("span", class_="prog_name")
    expo_org_span = new_day_table.find("span", class_="expo_org")
    prog_name_span_a = prog_name_span.find("a")

    hours_str, minuts_str = min_span.text.strip().split(":")

    return Program(
        title=prog_name_span.text.strip(),
        url=HttpUrl("https://www.tv-asahi.co.jp/" + prog_name_span_a["href"]),
        description=expo_org_span.text.strip() if expo_org_span else "",
        start=calc_start_from_date_hours_and_minutes(
            date=date, hours=int(hours_str), minutes=int(minuts_str)
        ),
    )


def parse_bangumi_list_td(
    bangumi_list_td, date: datetime.datetime
) -> tuple[Program, ...]:
    new_day_tables = bangumi_list_td.find_all("table", class_="new_day")

    return tuple(
        parse_new_day_table(new_day_table, date) for new_day_table in new_day_tables
    )


def parse_html(html: str) -> tuple[Program, ...]:
    soup = BeautifulSoup(html, "html.parser")

    tt_day_tr = soup.find("tr", id="ttDay")
    if not isinstance(tt_day_tr, Tag):
        raise ValueError("ttDay not found")

    dates = [
        parse_day_str(td.text.strip())
        for td in tt_day_tr.find_all("td", class_=lambda x: x != "none")
    ]

    bangumi_list_tds = soup.find_all("td", attrs={"valign": "top"})

    assert len(dates) == len(bangumi_list_tds) == 7

    return tuple(
        itertools.chain.from_iterable(
            parse_bangumi_list_td(td, date) for td, date in zip(bangumi_list_tds, dates)
        )
    )


async def fetch_programs(client: httpx.AsyncClient, url: str) -> tuple[Program, ...]:
    response = await fetch_with_retry(client, url)
    html = response.text

    return parse_html(html)


class TvAsahi(Channel):
    @property
    def channel_name(self) -> str:
        return "テレビ朝日"

    @alru_cache(ttl=60 * 5)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        urls = [
            "https://www.tv-asahi.co.jp/bangumi/index.html",
            "https://www.tv-asahi.co.jp/bangumi/next.html",
        ]
        tasks = [fetch_programs(client, url) for url in urls]
        results = await asyncio.gather(*tasks)
        programs = list(itertools.chain.from_iterable(results))

        return Schedule(
            channel_name=self.channel_name,
            channel_url=HttpUrl("https://www.tv-asahi.co.jp/bangumi/"),
            programs=programs,
        )


tv_asahi = TvAsahi()
