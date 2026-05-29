import httpx
import pytest

from app.main import path_to_channel


@pytest.mark.parametrize("path", path_to_channel.keys())
async def test_fetch_schedule_scrapes_programs(
    path: str, http_client: httpx.AsyncClient
) -> None:
    schedule = await path_to_channel[path].fetch_schedule(http_client)

    assert schedule.channel_name
    assert schedule.programs

    for program in schedule.programs:
        assert program.title.strip()
        assert program.start.tzinfo is not None
