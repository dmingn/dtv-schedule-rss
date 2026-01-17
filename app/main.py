from xml.etree.ElementTree import tostring

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse

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
from app.lifespan import lifespan

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


@app.get("/", response_class=HTMLResponse)
async def get_top_page() -> str:
    html_links = "".join(
        [
            f'<li><a href="/{path}">{channel.channel_name}</a></li>'
            for path, channel in path_to_channel.items()
        ]
    )

    return f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <title>テレビ番組表 RSS フィード</title>
    <style>
        body {{
            font-family: sans-serif;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
        }}
        h1 {{ color: #333; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>テレビ番組表 RSS フィード</h1>
    <ul>
        {html_links}
    </ul>
</body>
</html>
"""


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
