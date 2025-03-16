import datetime
import itertools

import requests
from bs4 import BeautifulSoup
from cachetools.func import ttl_cache
from pydantic import HttpUrl

from app.channel import Channel, Program, Schedule


def parse_td_item(td) -> Program:
    txta_span = td.find("span", class_="txtA")

    return Program(
        title=td.find("strong").text.strip(),
        url="https://www.tbs.co.jp/tv/" + td.find("a")["href"],
        description=txta_span.text.strip() if txta_span else None,
        start=datetime.datetime.strptime(
            td.find("span", class_="starttime").text.strip() + " +09:00",
            "%Y%m%d%H%M %z",
        ),
    )


def parse_html(html: str) -> tuple[Program, ...]:
    soup = BeautifulSoup(html, "html.parser")

    tds = soup.find_all("td", class_=lambda x: x != "empty")

    return tuple(parse_td_item(td) for td in tds)


@ttl_cache(ttl=60 * 5)
def fetch_programs(url: str) -> tuple[Program, ...]:
    response = requests.get(url)
    html = response.content.decode(response.apparent_encoding)

    return parse_html(html)


class Tbs(Channel):
    def fetch_schedule(self) -> Schedule:
        programs = list(
            itertools.chain.from_iterable(
                fetch_programs(url)
                for url in [
                    "https://www.tbs.co.jp/tv/index.html",
                    "https://www.tbs.co.jp/tv/nextweek.html",
                ]
            )
        )

        return Schedule(
            channel_name="TBSテレビ",
            channel_url=HttpUrl("https://www.tbs.co.jp/tv/index.html"),
            programs=programs,
        )


tbs = Tbs()
