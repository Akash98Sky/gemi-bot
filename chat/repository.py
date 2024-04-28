import asyncio
from aiogram.types import Message
from google.generativeai.generative_models import content_types, ChatSession

from chat.prompt_generator import PromptGenerator
from chat.services.gemini import GeminiService
from chat.query_processor import QueryProcessor

class Chat():
    __id: int
    __session: ChatSession
    __processor: QueryProcessor
    __generator: PromptGenerator
    __chat_init_history: list[content_types.glm.Content]
    __sem = asyncio.BoundedSemaphore(1)

    def __init__(self, id: int, session: ChatSession, processor: QueryProcessor, generator: PromptGenerator) -> None:
        self.__id = id
        self.__session = session
        self.__processor = processor
        self.__chat_init_history = session.history
        self.__generator = generator

    async def send_message_async(self, received: Message, sent: Message):
        async with self.__sem:
            # generate new response only if earlier responses are complete
            prompts = await self.__generator.generate(received)

            async for reply in self.__processor.process_response(session=self.__session, messages=prompts, chat_id=self.__id, rcvd_msg_id=received.message_id, sent_msg_id=sent.message_id):
                yield reply
    
    async def reset(self):
        self.__session.history.clear()
        self.__session.history.extend(self.__chat_init_history)

class ChatRepo():
    __gemini: GeminiService
    __chats: dict[int, Chat]
    __chat_creation_sem = asyncio.BoundedSemaphore(1)
    __query_processor: QueryProcessor
    __prompt_generator: PromptGenerator

    def __init__(self, gemini: GeminiService, processor: QueryProcessor, generator: PromptGenerator) -> None:
        self.__gemini = gemini
        self.__chats = {}
        self.__query_processor = processor
        self.__prompt_generator = generator

    async def get_chat_session(self, chat_id: int):
        async with self.__chat_creation_sem:
            if chat_id not in self.__chats.keys():
                session = self.__gemini.create_chat_session()
                self.__chats[chat_id] = Chat(id=chat_id, session=session, processor=self.__query_processor, generator=self.__prompt_generator)
        return self.__chats[chat_id]
    