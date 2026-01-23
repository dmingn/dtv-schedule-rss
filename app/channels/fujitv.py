import asyncio
import datetime
import itertools

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule
from app.utils.http import fetch_json_with_retry


def parse_datetime(datetime_str: str) -> datetime.datetime:
    date_str = datetime_str[:10]
    hours_str, minutes_str, seconds_str = datetime_str[11:19].split(":")

    return datetime.datetime.fromisoformat(
        date_str + "T00:00:00 +09:00"
    ) + datetime.timedelta(
        hours=int(hours_str), minutes=int(minutes_str), seconds=int(seconds_str)
    )


class FujitvProgram(BaseModel):
    title: str
    url: str
    overview: str
    start: str

    def to_program(self) -> Program:
        return Program(
            title=self.title,
            url=HttpUrl(self.url) if self.url else None,
            description=self.overview,
            start=parse_datetime(self.start),
        )


async def fetch_fujitv_programs(
    client: httpx.AsyncClient, date: datetime.date
) -> tuple[FujitvProgram, ...]:
    url = (
        f"https://www.fujitv.co.jp/bangumi/json/timetable_{date.strftime('%Y%m%d')}.js"
    )
    response_json = await fetch_json_with_retry(client, url)

    return tuple(
        FujitvProgram.model_validate(item) for item in response_json["contents"]["item"]
    )


class Fujitv(Channel):
    @property
    def channel_name(self) -> str:
        return "フジテレビ"

    @alru_cache(ttl=60 * 5)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        today = datetime.date.today()
        dates = [today + datetime.timedelta(days=i) for i in range(7)]

        tasks = [fetch_fujitv_programs(client, date) for date in dates]
        results = await asyncio.gather(*tasks)
        fujitv_programs = itertools.chain.from_iterable(results)

        return Schedule(
            channel_name=self.channel_name,
            channel_url=HttpUrl("https://www.fujitv.co.jp/timetable/weekly/"),
            programs=[p.to_program() for p in fujitv_programs],
        )


fujitv = Fujitv()
