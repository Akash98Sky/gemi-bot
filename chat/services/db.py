import asyncio
from aiogram import types as tg
from prisma.client import Prisma
from prisma.types import *
import prisma.models

class DbService:
    __db: Prisma
    __db_sem = asyncio.BoundedSemaphore(1)

    def __init__(self):
        self.__db = Prisma()

    async def db(self):
        async with self.__db_sem:
            if not self.__db.is_connected():
                await self.__db.connect()
        return self.__db

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
    
    async def insert_messages(self, chat_id: int, messages: list[tg.Message]):
        db = await self.db()
        return await db.message.create_many(
            data=[
                MessageCreateWithoutRelationsInput(
                    id=message.message_id,
                    text=message.text if message.text else '',
                    userId=message.from_user.id if message.from_user else None,
                    chatId=chat_id
                ) for message in messages
            ]
        )

    def disconnect(self):
        self.__db.disconnect()
