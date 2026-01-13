import datetime
import itertools
from typing import Literal

import requests
from cachetools.func import ttl_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule


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


@ttl_cache(ttl=60 * 5)
def fetch_broadcast_events(
    service_id: str, area_id: str, date: datetime.date
) -> tuple[BroadcastEvent, ...]:
    url = (
        f"https://api.nhk.jp/r7/pg/date/{service_id}/{area_id}/{date.isoformat()}.json"
    )
    response = requests.get(url)
    response_json = response.json()

    return tuple(
        BroadcastEvent.model_validate(d)
        for d in response_json[service_id]["publication"]
    )


class Nhk(Channel):
    def __init__(self, channel_name: str, service_id: str, area_id: str):
        super().__init__()
        self.channel_name = channel_name
        self.service_id = service_id
        self.area_id = area_id

    def fetch_schedule(self) -> Schedule:
        broadcast_events = itertools.chain.from_iterable(
            fetch_broadcast_events(
                service_id=self.service_id,
                area_id=self.area_id,
                date=date,
            )
            for date in (
                datetime.date.today() + datetime.timedelta(days=i) for i in range(7)
            )
        )

        return Schedule(
            channel_name=self.channel_name,
            channel_url=HttpUrl(f"https://www.nhk.jp/timetable/{self.area_id}/tv/"),
            programs=[
                broadcast_event.to_program() for broadcast_event in broadcast_events
            ],
        )


nhk_g1_130 = Nhk(channel_name="NHK総合1・東京", service_id="g1", area_id="130")
nhk_e1_130 = Nhk(channel_name="NHK Eテレ1・東京", service_id="e1", area_id="130")
