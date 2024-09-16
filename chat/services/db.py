import asyncio
from aiogram import types as tg
from prisma.client import Prisma
from prisma.types import *
import prisma.models
from motor.motor_asyncio import AsyncIOMotorClient

from common.models.embedded_message import EmbeddedMessage
from common.models.scored_message import ScoredMessage

class DbService:
    __db: Prisma
    __motor_db: AsyncIOMotorClient
    __db_sem = asyncio.BoundedSemaphore(1)

    def __init__(self, url: str):
        self.__db = Prisma()
        self.__motor_db = AsyncIOMotorClient(url)

    async def db(self):
        async with self.__db_sem:
            if not self.__db.is_connected():
                await self.__db.connect()
        return self.__db
    
    def motor(self):
        return self.__motor_db.get_default_database()

    async def upsert_chat_users(self, chat: tg.Chat, users: list[tg.User] = []):
        db = await self.db()
        
        if len(users) > 0:
            batch = db.batch_()
            for user in users:
                batch.user.upsert(
                    where={
                        'id': user.id
                    },
                    data={
                        'create': UserCreateInput(
                            id=user.id,
                            username=user.username,
                            firstName=user.first_name,
                            lastName=user.last_name,
                        ),
                        'update': UserUpdateInput(
                            username=user.username,
                            firstName=user.first_name,
                            lastName=user.last_name,
                        )
                    }
                )
            await batch.commit()

        return await db.chat.upsert(
            where={
                'id': chat.id
            },
            data={
                'create': ChatCreateInput(
                    id=chat.id,
                    title=chat.title if chat.title else chat.username,
                    users=UserUpdateManyWithoutRelationsInput(
                        connect=[ { 'id': user.id } for user in users ]
                    )
                ),
                'update': ChatUpdateInput(
                    title=chat.title if chat.title else chat.username,
                    users=UserUpdateManyWithoutRelationsInput(
                        connect=[ { 'id': user.id } for user in users ]
                    )
                )
            },
            include={
                'users': True
            }
        )
    
    async def get_user(self, id: int):
        db = await self.db()
        return await db.user.find_unique(
            where={
                'id': id
            }
        )
    
    async def insert_messages(self, chat_id: int, messages: list[EmbeddedMessage]):
        db = await self.db()
        batch = db.batch_()
        for msg in messages:
            batch.message.create(
                data=MessageCreateInput(
                    uniqueId=f'{chat_id}:{msg.message.message_id}',
                    messageId=msg.message.message_id,
                    parent=ParentMessageCreateNestedWithoutRelationsInput(
                        create={ 'uniqueId': f'{chat_id}:{msg.parent_msg_id}' } if msg.parent_msg_id else None,
                        connect={ 'uniqueId' : f'{chat_id}:{msg.parent_msg_id}' } if msg.parent_msg_id else None
                    ),
                    text=msg.message.text if msg.message.text else '',
                    textEmbedding=msg.embedding,
                    userId=msg.message.from_user.id if msg.message.from_user else None,
                    chatId=chat_id
                )
            )
        await batch.commit()
    
    async def aggregate_messages(self, chat_id: int, query_vector: list[float], dimension: int = 1024):
        db = self.motor()
        res_list: list[ScoredMessage] = []
        for doc in await db.Message.aggregate([
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "textEmbedding",
                    "queryVector": query_vector,
                    "numCandidates": dimension,
                    "limit": 10,
                    "filter": {
                        "chatId": {"$eq": chat_id}
                    }
                }
            },
            {
                "$project": {
                    "textEmbedding":0,
                    "score": {
                        '$meta': 'vectorSearchScore'
                    }
                }
            }
        ]).to_list(length=10):
            res_list.append(ScoredMessage(
                message=models.Message(
                    objId=str(doc['_id']),
                    id=doc['id'],
                    text=doc['text'],
                    textEmbedding=[],
                    userId=doc['userId'],
                    chatId=doc['chatId'],
                    createdAt=doc['createdAt'] if 'createdAt' in doc else datetime.datetime.now(),
                ),
                score=doc['score']
            ))

        return res_list

    def disconnect(self):
        self.__db.disconnect()
