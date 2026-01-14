import asyncio
import datetime
import itertools
from typing import Literal
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field, HttpUrl

from app.channel import Channel, Program, Schedule
from app.utils.cache import async_ttl_cache
from app.utils.http import fetch_with_retry

MxTvChannel = Literal[1, 2]


class TokyoMxProgram(BaseModel):
    start_time: str = Field(alias="Start_time")
    event_name: str = Field(alias="Event_name")
    event_text: str = Field(alias="Event_text")
    event_detail: str = Field(alias="Event_detail")

    def to_program(self, mxtv_channel: MxTvChannel) -> Program:
        start = datetime.datetime.strptime(
            self.start_time, "%Y年%m月%d日%H時%M分%S秒"
        ).replace(tzinfo=ZoneInfo("Asia/Tokyo"))

        url = f"https://s.mxtv.jp/bangumi/program.html?date={start.strftime('%Y%m%d')}&ch={mxtv_channel}&hm={start.strftime('%H%M')}"

        return Program(
            title=self.event_name,
            url=HttpUrl(url),
            description="\n".join([self.event_text, self.event_detail]).strip(),
            start=start,
        )


async def fetch_mxtv_programs(
    client: httpx.AsyncClient, mxtv_channel: MxTvChannel, date: datetime.datetime
) -> tuple[TokyoMxProgram, ...]:
    url = f"https://s.mxtv.jp/bangumi_file/json01/SV{mxtv_channel}EPG{date.strftime('%Y%m%d')}.json"
    response = await fetch_with_retry(client, url)
    response_json = response.json()

    return tuple(TokyoMxProgram.model_validate(item) for item in response_json)


async def get_programs(
    client: httpx.AsyncClient, mxtv_channel: MxTvChannel, date: datetime.datetime
) -> tuple[Program, ...]:
    mxtv_programs = await fetch_mxtv_programs(
        client=client, mxtv_channel=mxtv_channel, date=date
    )
    return tuple(p.to_program(mxtv_channel) for p in mxtv_programs)


class MxTv(Channel):
    def __init__(self, channel: MxTvChannel):
        super().__init__()
        self.channel = channel

    @async_ttl_cache(ttl=60 * 5)
    async def fetch_schedule(self, client: httpx.AsyncClient) -> Schedule:
        today = datetime.datetime.now(tz=ZoneInfo("Asia/Tokyo")).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        dates = [today + datetime.timedelta(days=i) for i in range(7)]

        tasks = [get_programs(client, self.channel, date) for date in dates]
        results = await asyncio.gather(*tasks)
        programs = list(itertools.chain.from_iterable(results))

        return Schedule(
            channel_name=f"TOKYO MX {self.channel}",
            channel_url=HttpUrl("https://s.mxtv.jp/bangumi/"),
            programs=programs,
        )


mx_tv_1 = MxTv(channel=1)
mx_tv_2 = MxTv(channel=2)
