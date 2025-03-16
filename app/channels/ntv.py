import datetime
import json
import time
from typing import Optional

import requests
from cachetools.func import ttl_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule


class ActualDatetime(BaseModel):
    broadcast_date: str
    start_time: str
    end_time: str


class NtvProgram(BaseModel):
    actual_datetime: ActualDatetime
    start_time: str
    end_time: str
    program_title_excluding_hanrei: str
    program_content: str
    program_detail: Optional[str] = None
    program_site_url: Optional[HttpUrl] = None

    def to_program(self) -> Program:
        return Program(
            title=self.program_title_excluding_hanrei,
            url=self.program_site_url,
            description=self.program_content
            + (("\n" + self.program_detail) if self.program_detail else ""),
            start=datetime.datetime.strptime(
                f"{self.actual_datetime.broadcast_date} {self.actual_datetime.start_time} +09:00",
                "%Y%m%d %H%M %z",
            ),
        )


@ttl_cache(ttl=60 * 5)
def fetch_ntv_programs() -> tuple[NtvProgram, ...]:
    url = f"https://www.ntv.co.jp/program/json/program_list.json?_={int(time.time() * 1000)}"
    response = requests.get(url)
    response_json = json.loads(response.content.decode(response.apparent_encoding))

    return tuple(NtvProgram.model_validate(d) for d in response_json)


class Ntv(Channel):
    def fetch_schedule(self) -> Schedule:
        ntv_programs = fetch_ntv_programs()

        return Schedule(
            channel_name="日本テレビ",
            channel_url=HttpUrl("https://www.ntv.co.jp/program/"),
            programs=[broadcast_event.to_program() for broadcast_event in ntv_programs],
        )


ntv = Ntv()
