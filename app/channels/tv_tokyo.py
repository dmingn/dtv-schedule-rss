import datetime
import itertools
import json
from zoneinfo import ZoneInfo

import requests
from cachetools.func import ttl_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule


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


@ttl_cache(ttl=60 * 5)
def fetch_tv_tokyo_programs(date: datetime.datetime) -> tuple[TvTokyoProgram, ...]:
    url = f"https://www.tv-tokyo.co.jp/tbcms/assets/data/{date.strftime('%Y%m%d')}.json"
    response = requests.get(url)
    response_json = json.loads(response.content.decode(response.apparent_encoding))

    items = [
        v["1"] for v in response_json.values() if "1" in v and v["1"]["start_time"]
    ]

    return tuple(TvTokyoProgram.model_validate(item) for item in items)


def get_programs(date: datetime.datetime) -> tuple[Program, ...]:
    tv_tokyo_programs = fetch_tv_tokyo_programs(date)
    return tuple(p.to_program(date) for p in tv_tokyo_programs)


class TvTokyo(Channel):
    def fetch_schedule(self) -> Schedule:
        programs = itertools.chain.from_iterable(
            get_programs(date)
            for date in (
                datetime.datetime.now(tz=ZoneInfo("Asia/Tokyo")).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                + datetime.timedelta(days=i)
                for i in range(7)
            )
        )

        return Schedule(
            channel_name="テレ東",
            channel_url=HttpUrl(
                "https://www.tv-tokyo.co.jp/timetable/broad_tvtokyo/thisweek/"
            ),
            programs=list(programs),
        )


tv_tokyo = TvTokyo()
