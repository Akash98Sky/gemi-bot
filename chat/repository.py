import asyncio
from aiogram import types as tg
from google.generativeai.generative_models import content_types, ChatSession

from chat.memorizer import Memorizer
from chat.prompt_generator import PromptGenerator
from chat.services.db import DbService, models as db
from chat.services.gemini import GeminiService
from chat.query_processor import QueryProcessor

class Chat():
    __data: db.Chat
    __session: ChatSession
    __processor: QueryProcessor
    __generator: PromptGenerator
    __memorizer: Memorizer
    __chat_init_history: list[content_types.glm.Content]
    __sem = asyncio.BoundedSemaphore(1)

    def __init__(self, data: db.Chat, session: ChatSession, processor: QueryProcessor, generator: PromptGenerator, memorizer: Memorizer) -> None:
        self.__data = data
        self.__session = session
        self.__processor = processor
        self.__chat_init_history = session.history
        self.__generator = generator
        self.__memorizer = memorizer

    def id(self):
        return self.__data.id
    
    def users(self):
        return self.__data.users if self.__data.users else []
    
    def memorize_messages(self, received: tg.Message, sent: tg.Message):
        asyncio.create_task(self.__memorizer.remember(self.id(), received, sent))

    async def send_message_async(self, received: tg.Message):
        async with self.__sem:
            # generate new response only if earlier responses are complete
            prompts = await self.__generator.generate(received)

            async for reply in self.__processor.process_response(session=self.__session, messages=prompts, chat_id=self.id()):
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
    __memorizer: Memorizer
    __db: DbService

    def __init__(self, gemini: GeminiService, processor: QueryProcessor, generator: PromptGenerator, db: DbService, memorizer: Memorizer) -> None:
        self.__gemini = gemini
        self.__chats = {}
        self.__query_processor = processor
        self.__prompt_generator = generator
        self.__db = db
        self.__memorizer = memorizer

    async def get_chat_session(self, chat: tg.Chat, users: list[tg.User] = []) -> Chat:
        async with self.__chat_creation_sem:
            if chat.id not in self.__chats.keys():
                db_chat = await self.__db.upsert_chat_users(chat, users)
                
                session = self.__gemini.create_chat_session()
                self.__chats[chat.id] = Chat(
                    data=db_chat,
                    session=session,
                    processor=self.__query_processor,
                    generator=self.__prompt_generator,
                    memorizer=self.__memorizer
                )
        
        # existing chat session
        chat_session = self.__chats[chat.id]

        existing_userids = [user.id for user in chat_session.users()]
        new_users = [user for user in users if user.id not in existing_userids]
        if any(new_users):
            # update chat and user records if any new user is found
            db_chat = await self.__db.upsert_chat_users(chat, new_users)
            chat_session.__data = db_chat

        return chat_session
    