import datetime
import itertools
import json
from typing import Literal
from zoneinfo import ZoneInfo

import requests
from cachetools.func import ttl_cache
from pydantic import BaseModel, Field, HttpUrl

from app.channel import Channel, Program, Schedule

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


@ttl_cache(ttl=60 * 5)
def fetch_mxtv_programs(
    mxtv_channel: MxTvChannel, date: datetime.datetime
) -> tuple[TokyoMxProgram, ...]:
    url = f"https://s.mxtv.jp/bangumi_file/json01/SV{mxtv_channel}EPG{date.strftime('%Y%m%d')}.json"
    response = requests.get(url)
    response_json = json.loads(response.content.decode(response.apparent_encoding))

    return tuple(TokyoMxProgram.model_validate(item) for item in response_json)


def get_programs(
    mxtv_channel: MxTvChannel, date: datetime.datetime
) -> tuple[Program, ...]:
    mxtv_programs = fetch_mxtv_programs(mxtv_channel=mxtv_channel, date=date)
    return tuple(p.to_program(mxtv_channel) for p in mxtv_programs)


class MxTv(Channel):
    def __init__(self, channel: MxTvChannel):
        super().__init__()
        self.channel = channel

    def fetch_schedule(self) -> Schedule:
        programs = list(
            itertools.chain.from_iterable(
                get_programs(mxtv_channel=self.channel, date=date)
                for date in (
                    datetime.datetime.now(tz=ZoneInfo("Asia/Tokyo")).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=i)
                    for i in range(7)
                )
            )
        )

        return Schedule(
            channel_name="TOKYO MX",
            channel_url=HttpUrl("https://s.mxtv.jp/bangumi/"),
            programs=programs,
        )


mx_tv_1 = MxTv(channel=1)
mx_tv_2 = MxTv(channel=2)
