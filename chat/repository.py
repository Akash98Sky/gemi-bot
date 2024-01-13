import asyncio
from typing import Iterable, Union
from google.generativeai.generative_models import content_types, ChatSession

from chat.service import ChatService
from chat.query_processor import QueryProcessor

class Chat():
    __id: int
    __session: ChatSession
    __processor: QueryProcessor
    __sem = asyncio.BoundedSemaphore(1)

    def __init__(self, id: int, session: ChatSession, processor: QueryProcessor):
        self.__id = id
        self.__session = session
        self.__processor = processor

    async def send_message_async(self, messages: Union[Iterable[content_types.PartType], str]):
        async with self.__sem:
            # generate new response only if earlier responses are complete
            async for reply in self.__processor.process_response(session=self.__session, messages=messages, chat_id=self.__id):
                yield reply

class ChatRepo():
    __service: ChatService
    __chats: dict[int, Chat]
    __chat_creation_sem = asyncio.BoundedSemaphore(1)
    __query_processor: QueryProcessor

    def __init__(self, service: ChatService, processor: QueryProcessor) -> None:
        self.__service = service
        self.__chats = {}
        self.__query_processor = processor

    async def get_chat_session(self, chat_id: int):
        async with self.__chat_creation_sem:
            if chat_id not in self.__chats.keys():
                session = self.__service.create_chat_session()
                self.__chats[chat_id] = Chat(id=chat_id, session=session, processor=self.__query_processor)
        return self.__chats[chat_id]
    