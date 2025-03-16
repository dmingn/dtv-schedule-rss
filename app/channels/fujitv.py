import datetime
import itertools
import json

import requests
from cachetools.func import ttl_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule


def parse_datetime(datetime_str: str) -> datetime.datetime:
    date_str, rest = datetime_str.split("T")
    hours_str, minutes_str, seconds_str = rest.split("W")[0].split(":")

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


@ttl_cache(ttl=60 * 5)
def fetch_fujitv_programs(date: datetime.date) -> tuple[FujitvProgram, ...]:
    url = (
        f"https://www.fujitv.co.jp/bangumi/json/timetable_{date.strftime('%Y%m%d')}.js"
    )
    response = requests.get(url)
    response_json = json.loads(response.content.decode(response.apparent_encoding))

    return tuple(
        FujitvProgram.model_validate(item) for item in response_json["contents"]["item"]
    )


class Fujitv(Channel):
    def fetch_schedule(self) -> Schedule:
        fujitv_programs = itertools.chain.from_iterable(
            fetch_fujitv_programs(date)
            for date in (
                datetime.date.today() + datetime.timedelta(days=i) for i in range(7)
            )
        )

        return Schedule(
            channel_name="フジテレビ",
            channel_url=HttpUrl("https://www.fujitv.co.jp/timetable/weekly/"),
            programs=[p.to_program() for p in fujitv_programs],
        )


fujitv = Fujitv()
