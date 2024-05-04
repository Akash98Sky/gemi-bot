import asyncio
from aiogram import types as tg
from prisma.client import Prisma
from prisma.types import *
import prisma.models
from motor.motor_asyncio import AsyncIOMotorClient

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
    
    async def insert_messages(self, chat_id: int, messages: list[tg.Message], embeddings: list[list[float]]):
        db = await self.db()
        return await db.message.create_many(
            data=[
                MessageCreateWithoutRelationsInput(
                    id=message.message_id,
                    text=message.text if message.text else '',
                    textEmbedding=embeddings[i] if len(embeddings) > i else [],
                    userId=message.from_user.id if message.from_user else None,
                    chatId=chat_id
                ) for i, message in enumerate(messages)
            ]
        )
    
    async def aggregate_messages(self, chat_id: int, query_vector: list[float]):
        db = self.motor()
        res_list: list[ScoredMessage] = []
        for doc in await db.Message.aggregate([
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "textEmbedding",
                    "queryVector": query_vector,
                    "numCandidates": 768,
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
