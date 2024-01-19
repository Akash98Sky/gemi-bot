from typing import Any, Dict
from aiohttp.web import RouteTableDef, Request, json_response

from containers import BotContainer

routes = RouteTableDef()

@routes.get("/")
async def root(request: Request):
    q = request.query.get('q', None)
    if q is None or q.isspace():
        return json_response({ "message": "Hello World" })
    res = ''.join([r async for r in BotContainer.chat_service().gen_response(q)])
    return json_response({"message": q, "reply": res})

@routes.get("/ping")
async def ping(_: Request):
    return json_response({"message": "pong"})

@routes.get("/set_webhook")
async def set_webhook(_: Request):
    res = await BotContainer.tg_bot().set_webhook()
    return json_response({"success": res})

@routes.get("/reset_webhook")
async def reset_webhook(_: Request):
    res = await BotContainer.tg_bot().delete_webhook()
    return json_response({"success": res})
