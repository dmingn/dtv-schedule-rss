import abc
import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl

from app import rss


class Program(BaseModel):
    title: str
    url: Optional[HttpUrl]
    description: Optional[str]
    start: datetime.datetime

    def to_rss_item(self) -> rss.Item:
        return rss.Item(
            title=self.title,
            link=self.url,
            description=self.description,
            pub_date=self.start,
        )


class Schedule(BaseModel):
    channel_name: str
    channel_url: HttpUrl
    programs: list[Program]

    def to_rss_channel(self) -> rss.Channel:
        return rss.Channel(
            title=self.channel_name,
            link=self.channel_url,
            description="",
            item=[program.to_rss_item() for program in self.programs],
        )


class Channel(abc.ABC):
    @abc.abstractmethod
    def fetch_schedule(self) -> Schedule:
        pass
