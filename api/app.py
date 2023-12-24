from asyncio import sleep
from typing import Any, Dict, Annotated, Union
from fastapi import Depends, FastAPI, Request
from aiohttp import ClientSession
from os import getenv

from chat.service import ChatService
from containers import BotContainer

app = FastAPI()


@app.get("/")
async def root(chat_service: Annotated[ChatService, Depends(lambda: BotContainer.chat_service())], q: Union[str, None] = None) -> Dict[str, Any]:
    if q is None:
        return { "message": "Hello World" }
    res = await chat_service.gen_response(q)
    return {"message": q, "reply": res}

@app.get("/ping")
async def ping():
    return {"message": "pong"}

@app.get("/keepawake")
async def ping(secs: int = 20):
    # keep awake for n sec
    await sleep(secs)
    return {"message": "awake for " + str(secs) + " secs"}

@app.post("/__space/v0/actions")
async def actions(req: Request):
    body = await req.json()
    if(body['event']['id'] == 'wakeup'):
        async with ClientSession(conn_timeout=20) as session:
            async with session.get(req.base_url.scheme + '://' + getenv('DETA_SPACE_APP_HOSTNAME') + '/keepawake?secs=50') as res:
                return await res.text()