from xml.etree.ElementTree import tostring

from fastapi import FastAPI, Response
from app.http_client import lifespan

from app.channel import Channel
from app.channels import (
    fujitv,
    mx_tv_1,
    mx_tv_2,
    nhk_e1_130,
    nhk_g1_130,
    ntv,
    tbs,
    tv_asahi,
    tv_tokyo,
)

path_to_channel: dict[str, Channel] = {
    "joak-dtv": nhk_g1_130,
    "joab-dtv": nhk_e1_130,
    "joax-dtv": ntv,
    "jorx-dtv": tbs,
    "jocx-dtv": fujitv,
    "joex-dtv": tv_asahi,
    "jotx-dtv": tv_tokyo,
    "jomx-dtv-1": mx_tv_1,
    "jomx-dtv-2": mx_tv_2,
}


app = FastAPI(lifespan=lifespan)


@app.get("/{path}")
async def get_schedule_rss(path: str) -> Response:
    if path not in path_to_channel:
        return Response(status_code=404)

    client = app.state.http_client
    schedule = await path_to_channel[path].fetch_schedule(client)

    return Response(
        content=tostring(schedule.to_rss_channel().to_xml()),
        media_type="application/xml",
    )
