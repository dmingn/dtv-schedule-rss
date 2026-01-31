import asyncio
import datetime
import itertools
import logging

import httpx
from async_lru import alru_cache
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from app.channel import Channel, Program, Schedule
from app.config import settings
from app.utils.http import fetch_text_with_retry

logger = logging.getLogger(__name__)


def parse_td_item(td) -> Program:
    txta_span = td.find("span", class_="txtA")

    return Program(
        title=td.find("strong").text.strip(),
        url="https://www.tbs.co.jp/tv/" + td.find("a")["href"],
        description=txta_span.text.strip() if txta_span else None,
        start=datetime.datetime.strptime(
            td.find("span", class_="starttime").text.strip() + " +09:00",
            "%Y%m%d%H%M %z",
        ),
    )


def parse_html(html: str) -> tuple[Program, ...]:
    soup = BeautifulSoup(html, "html.parser")

    tds = soup.find_all("td", class_=lambda x: x != "empty")

    return tuple(parse_td_item(td) for td in tds)


async def fetch_programs(client: httpx.AsyncClient, url: str) -> tuple[Program, ...]:
    html = await fetch_text_with_retry(client, url)

    try:
        return parse_html(html)
    except (ValueError, AttributeError):
        html_preview = html[:500] if html else "(empty)"
        logger.exception(f"HTML parse error for {url}, html_preview={html_preview!r}")
        raise


class Tbs(Channel):
    @property
    def channel_name(self) -> str:
        return "TBSテレビ"

    @alru_cache(ttl=settings.schedule_cache_ttl_seconds)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        urls = [
            "https://www.tbs.co.jp/tv/index.html",
            "https://www.tbs.co.jp/tv/nextweek.html",
        ]
        tasks = [fetch_programs(client, url) for url in urls]
        results = await asyncio.gather(*tasks)
        programs = list(itertools.chain.from_iterable(results))

        return Schedule(
            channel_name=self.channel_name,
            channel_url=HttpUrl("https://www.tbs.co.jp/tv/index.html"),
            programs=programs,
        )


tbs = Tbs()
