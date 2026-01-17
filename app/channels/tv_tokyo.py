import asyncio
import datetime
import itertools
from zoneinfo import ZoneInfo

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule
from app.utils.http import fetch_with_retry


def calc_start_from_date_hours_and_minutes(
    date: datetime.datetime, hours: int, minutes: int
) -> datetime.datetime:
    return date + datetime.timedelta(
        days=1 if hours < 4 else 0, hours=hours, minutes=minutes
    )


class TvTokyoProgram(BaseModel):
    url: str
    start_time: str
    title: str
    description: str

    def to_program(self, date: datetime.datetime) -> Program:
        hours_str, minutes_str = self.start_time.split(":")

        return Program(
            title=self.title,
            url=HttpUrl("https:" + self.url),
            description=self.description,
            start=calc_start_from_date_hours_and_minutes(
                date, int(hours_str), int(minutes_str)
            ),
        )


async def fetch_tv_tokyo_programs(
    client: httpx.AsyncClient, date: datetime.datetime
) -> tuple[TvTokyoProgram, ...]:
    url = f"https://www.tv-tokyo.co.jp/tbcms/assets/data/{date.strftime('%Y%m%d')}.json"
    response = await fetch_with_retry(client, url)
    response_json = response.json()

    items = [
        v["1"] for v in response_json.values() if "1" in v and v["1"]["start_time"]
    ]

    return tuple(TvTokyoProgram.model_validate(item) for item in items)


async def get_programs(
    client: httpx.AsyncClient, date: datetime.datetime
) -> tuple[Program, ...]:
    tv_tokyo_programs = await fetch_tv_tokyo_programs(client, date)
    return tuple(p.to_program(date) for p in tv_tokyo_programs)


class TvTokyo(Channel):
    @alru_cache(ttl=60 * 5)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        today = datetime.datetime.now(tz=ZoneInfo("Asia/Tokyo")).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        dates = [today + datetime.timedelta(days=i) for i in range(7)]

        tasks = [get_programs(client, date) for date in dates]
        results = await asyncio.gather(*tasks)
        programs = list(itertools.chain.from_iterable(results))

        return Schedule(
            channel_name="テレ東",
            channel_url=HttpUrl(
                "https://www.tv-tokyo.co.jp/timetable/broad_tvtokyo/thisweek/"
            ),
            programs=programs,
        )


tv_tokyo = TvTokyo()
