from logging import Logger, getLogger
from aiogram import types as tg

from chat.services.db import DbService

logging: Logger = getLogger(__name__)

class Memorizer:
    __db: DbService

    def __init__(self, db: DbService):
        self.__db = db

    async def remember(self, chat_id: int, received: tg.Message, sent: tg.Message):
        try:
            await self.__db.insert_messages(chat_id, [received, sent])
        except Exception as e:
            logging.warning(f"Failed to remember messages from chat {chat_id}, Exception: {e}", exc_info=True)

    def recall(self, chat_id: int):
        pass