import datetime
from xml.etree.ElementTree import Element

from pydantic import AwareDatetime, BaseModel, HttpUrl


def datetime_to_rfc822(dt: datetime.datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


class Item(BaseModel):
    title: str | None = None
    link: HttpUrl | None = None
    description: str | None = None
    pub_date: AwareDatetime | None = None

    def to_xml(self) -> Element:
        item = Element("item")

        if self.title:
            title = Element("title")
            title.text = self.title
            item.append(title)

        if self.link:
            link = Element("link")
            link.text = str(self.link)
            item.append(link)

        if self.description:
            description = Element("description")
            description.text = self.description
            item.append(description)

        if self.pub_date:
            pub_date = Element("pubDate")
            pub_date.text = datetime_to_rfc822(self.pub_date)
            item.append(pub_date)

        return item


class Channel(BaseModel):
    title: str
    link: HttpUrl
    description: str
    item: list[Item] | None = None

    def to_xml(self) -> Element:
        rss = Element("rss")
        rss.set("version", "2.0")

        channel = Element("channel")
        rss.append(channel)

        title = Element("title")
        title.text = self.title
        channel.append(title)

        link = Element("link")
        link.text = str(self.link)
        channel.append(link)

        description = Element("description")
        description.text = self.description
        channel.append(description)

        if self.item:
            for item in self.item:
                channel.append(item.to_xml())

        return rss
