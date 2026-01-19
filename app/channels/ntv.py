import datetime
import time

import httpx
from async_lru import alru_cache
from pydantic import BaseModel, HttpUrl

from app.channel import Channel, Program, Schedule
from app.utils.http import fetch_with_retry


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
    program_detail: str | None = None
    program_site_url: HttpUrl | None = None

    def to_program(self) -> Program:
        return Program(
            title=self.program_title_excluding_hanrei,
            url=self.program_site_url,
            description=self.program_content
            + (("\n" + self.program_detail) if self.program_detail else ""),
            start=datetime.datetime.strptime(
                (
                    f"{self.actual_datetime.broadcast_date} "
                    f"{self.actual_datetime.start_time} +09:00"
                ),
                "%Y%m%d %H%M %z",
            ),
        )


async def fetch_ntv_programs(client: httpx.AsyncClient) -> tuple[NtvProgram, ...]:
    base_url = "https://www.ntv.co.jp/program/json/program_list.json"
    timestamp = int(time.time() * 1000)
    url = f"{base_url}?_={timestamp}"
    response = await fetch_with_retry(client, url)
    response_json = response.json()

    return tuple(NtvProgram.model_validate(d) for d in response_json)


class Ntv(Channel):
    @property
    def channel_name(self) -> str:
        return "日本テレビ"

    @alru_cache(ttl=60 * 5)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        ntv_programs = await fetch_ntv_programs(client)

        return Schedule(
            channel_name=self.channel_name,
            channel_url=HttpUrl("https://www.ntv.co.jp/program/"),
            programs=[broadcast_event.to_program() for broadcast_event in ntv_programs],
        )


ntv = Ntv()
