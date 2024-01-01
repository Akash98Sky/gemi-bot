import asyncio
from typing import Iterable, Union
from google.generativeai.generative_models import content_types, ChatSession
from chat.query_processor import QueryProcessor

from chat.service import ChatService

class Chat():
    __session: ChatSession
    __service: ChatService
    __processor: QueryProcessor
    __sem = asyncio.BoundedSemaphore(1)

    def __init__(self, service: ChatService, processor: QueryProcessor):
        self.__session = service.create_chat_session()
        self.__service = service
        self.__processor = processor

    async def send_message_async(self, messages: Union[Iterable[content_types.PartType], str]):
        async with self.__sem:
            # generate new response only if earlier responses are complete
            response = self.__service.gen_chat_response_stream(chat=self.__session, prompts=messages)
            on_query_cb = lambda q_prompt: self.__service.gen_chat_response_stream(chat=self.__session, prompts=[*messages, q_prompt])
            async for reply in self.__processor.intercepted_response(response, on_query_cb):
                yield reply

class ChatRepo():
    __service: ChatService
    __chats: dict[int, Chat]
    __chat_creation_sem = asyncio.BoundedSemaphore(1)
    __query_processor: QueryProcessor

    def __init__(self, service: ChatService) -> None:
        self.__service = service
        self.__chats = {}
        self.__query_processor = QueryProcessor()

    async def get_chat_session(self, chat_id: int):
        async with self.__chat_creation_sem:
            if chat_id not in self.__chats.keys():
                self.__chats[chat_id] = Chat(self.__service, self.__query_processor)
        return self.__chats[chat_id]
    