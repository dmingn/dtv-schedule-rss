import abc
import datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, HttpUrl

from app import rss


class Program(BaseModel):
    title: str
    url: Optional[HttpUrl]
    description: Optional[str]
    start: AwareDatetime

    @property
    def rss_description(self) -> str:
        return (
            self.start.strftime("%m/%d %H:%M") + "\n\n" + (self.description or "")
        ).strip()

    @property
    def rss_pub_date(self) -> datetime.datetime:
        # to make pubDate in the past, subtract 7 days from start for convenience
        return self.start - datetime.timedelta(days=7)

    def to_rss_item(self) -> rss.Item:
        return rss.Item(
            title=self.title,
            link=self.url,
            description=self.rss_description,
            pub_date=self.rss_pub_date,
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
