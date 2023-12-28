from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from io import BytesIO

class PhotoDownloadMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        data['has_photo'] = False
        if(event.photo and len(event.photo) > 0):
            photo_id = event.photo[0].file_id
            my_object = BytesIO()
            data['photo_bytes'] = await event.bot.download(photo_id, my_object)
            data['has_photo'] = True
        return await handler(event, data)

class ChatHistoryMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        reply_of = event.reply_to_message
        data['history'] = []
        while reply_of:
            data['history'].append(reply_of)
            reply_of = reply_of.reply_to_message
        return await handler(event, data)