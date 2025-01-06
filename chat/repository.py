import asyncio
from typing import Iterable, Union
from google.genai.chats import AsyncChat
from google.genai.types import Content, PartUnionDict

from chat.services.gemini import GeminiService
from chat.query_processor import QueryProcessor

class Chat():
    __id: int
    __session: AsyncChat
    __processor: QueryProcessor
    __chat_init_history: list[Content]
    __sem = asyncio.BoundedSemaphore(1)

    def __init__(self, id: int, session: AsyncChat, processor: QueryProcessor):
        self.__id = id
        self.__session = session
        self.__processor = processor
        self.__chat_init_history = session._curated_history

    async def send_message_async(self, messages: list[PartUnionDict]):
        async with self.__sem:
            # generate new response only if earlier responses are complete
            async for reply in self.__processor.process_response(session=self.__session, messages=messages, chat_id=self.__id):
                yield reply
    
    async def reset(self):
        self.__session._curated_history.clear()
        self.__session._curated_history.extend(self.__chat_init_history)

class ChatRepo():
    __gemini: GeminiService
    __chats: dict[int, Chat]
    __chat_creation_sem = asyncio.BoundedSemaphore(1)
    __query_processor: QueryProcessor

    def __init__(self, gemini: GeminiService, processor: QueryProcessor) -> None:
        self.__gemini = gemini
        self.__chats = {}
        self.__query_processor = processor

    async def get_chat_session(self, chat_id: int):
        async with self.__chat_creation_sem:
            if chat_id not in self.__chats.keys():
                session = self.__gemini.create_chat_session()
                self.__chats[chat_id] = Chat(id=chat_id, session=session, processor=self.__query_processor)
        return self.__chats[chat_id]
    