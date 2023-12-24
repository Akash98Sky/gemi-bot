from typing import Any, Dict, Annotated, Union
from fastapi import Depends, FastAPI

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