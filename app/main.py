from xml.etree.ElementTree import tostring

from fastapi import FastAPI, Response

from app.channel import Channel
from app.channels import fujitv, nhk_e1_130, nhk_g1_130, ntv, tbs

path_to_channel: dict[str, Channel] = {
    "joak-dtv": nhk_g1_130,
    "joab-dtv": nhk_e1_130,
    "joax-dtv": ntv,
    "jorx-dtv": tbs,
    "jocx-dtv": fujitv,
}


app = FastAPI()


@app.get("/{path}")
async def get_schedule_rss(path: str) -> Response:
    if path not in path_to_channel:
        return Response(status_code=404)

    return Response(
        content=tostring(
            path_to_channel[path].fetch_schedule().to_rss_channel().to_xml()
        ),
        media_type="application/xml",
    )
