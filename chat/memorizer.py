from logging import Logger, getLogger
from aiogram import types as tg
from google.generativeai.generative_models import content_types

from chat.services.db import DbService
from chat.services.gemini import GeminiService

logging: Logger = getLogger(__name__)

class Memorizer:
    __gemini: GeminiService
    __db: DbService

    def __init__(self, db: DbService, gemini: GeminiService):
        self.__db = db
        self.__gemini = gemini

    async def remember(self, chat_id: int, received: tg.Message, sent: tg.Message):
        try:
            msg_embedings = await self.__gemini.embed_contents([
                content_types.ContentDict(parts=[received.text], role="user"),
                content_types.ContentDict(parts=[sent.text], role="model")
            ])
            await self.__db.insert_messages(chat_id, [received, sent], msg_embedings)
        except Exception as e:
            logging.warning(f"Failed to remember messages from chat {chat_id}, Exception: {e}", exc_info=True)

    async def recall(self, chat_id: int, received: tg.Message):
        try:
            query_vector = await self.__gemini.embed_contents(content_types.ContentDict(parts=[received.text], role="user"))
            return await self.__db.aggregate_messages(chat_id, query_vector)
        except Exception as e:
            logging.warning(f"Failed to recall messages from chat {chat_id}, Exception: {e}", exc_info=True)