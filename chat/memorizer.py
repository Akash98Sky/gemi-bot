from logging import Logger, getLogger
from aiogram import types as tg
from google.generativeai.generative_models import content_types

from chat.services.cohere import CohereService
from chat.services.db import DbService
from common.models.embedded_message import EmbeddedMessage
from common.models.scored_message import ScoredMessage

logging: Logger = getLogger(__name__)

class Memorizer:
    __cohere: CohereService
    __db: DbService

    def __init__(self, db: DbService, cohere: CohereService):
        self.__db = db
        self.__cohere = cohere

    async def remember(self, chat_id: int, received: tg.Message, sent: tg.Message):
        try:
            msg_embedings = await self.__cohere.embed_texts([received.text, sent.text])
            embedded_messages = [
                EmbeddedMessage(received, embedding=msg_embedings[0], parent_msg_id=received.reply_to_message.message_id if received.reply_to_message else None),
                EmbeddedMessage(sent, embedding=msg_embedings[1], parent_msg_id=received.message_id)
            ]
            await self.__db.insert_messages(chat_id, embedded_messages)
        except Exception as e:
            logging.warning(f"Failed to remember messages from chat {chat_id}, Exception: {e}", exc_info=True)

    async def recall(self, chat_id: int, received: tg.Message):
        try:
            query_vector = await self.__cohere.embed_query(received.text)
            recalled = await self.__db.aggregate_messages(chat_id, query_vector)
            return list[ScoredMessage](filter(lambda scored: scored.score > 0.8, recalled))
        except Exception as e:
            logging.warning(f"Failed to recall messages from chat {chat_id}, Exception: {e}", exc_info=True)