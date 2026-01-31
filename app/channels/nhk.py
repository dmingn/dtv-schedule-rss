import asyncio
import datetime
import itertools
from typing import Literal

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule
from app.config import settings
from app.utils.http import fetch_json_with_retry


class About(BaseModel):
    canonical: HttpUrl | None = None


class BroadcastEvent(BaseModel):
    type: Literal["BroadcastEvent"]
    id: str
    name: str
    description: str
    startDate: datetime.datetime
    endDate: datetime.datetime
    about: About | None = None

    def to_program(self) -> Program:
        return Program(
            title=self.name,
            url=self.about.canonical if self.about else None,
            description=self.description,
            start=self.startDate,
        )


async def fetch_broadcast_events(
    client: httpx.AsyncClient, service_id: str, area_id: str, date: datetime.date
) -> tuple[BroadcastEvent, ...]:
    url = (
        f"https://api.nhk.jp/r7/pg/date/{service_id}/{area_id}/{date.isoformat()}.json"
    )
    response_json = await fetch_json_with_retry(client, url)

    return tuple(
        BroadcastEvent.model_validate(d)
        for d in response_json[service_id]["publication"]
    )


class Nhk(Channel):
    def __init__(self, channel_name: str, service_id: str, area_id: str):
        super().__init__()
        self._channel_name = channel_name
        self.service_id = service_id
        self.area_id = area_id

    @property
    def channel_name(self) -> str:
        return self._channel_name

    @alru_cache(ttl=settings.schedule_cache_ttl_seconds)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        today = datetime.date.today()
        dates = [today + datetime.timedelta(days=i) for i in range(7)]

        tasks = [
            fetch_broadcast_events(client, self.service_id, self.area_id, date)
            for date in dates
        ]
        results = await asyncio.gather(*tasks)
        broadcast_events = itertools.chain.from_iterable(results)

        return Schedule(
            channel_name=self.channel_name,
            channel_url=HttpUrl(f"https://www.nhk.jp/timetable/{self.area_id}/tv/"),
            programs=[
                broadcast_event.to_program() for broadcast_event in broadcast_events
            ],
        )


nhk_g1_130 = Nhk(channel_name="NHK総合1・東京", service_id="g1", area_id="130")
nhk_e1_130 = Nhk(channel_name="NHK Eテレ1・東京", service_id="e1", area_id="130")
