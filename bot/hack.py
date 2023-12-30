import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import Message
from aiohttp.web import Response
from os import getenv

from bot.enums import BotEventMethods
from utils.aiotimer import Timer

MSG_HANDLING_CONCURRENCY = int(getenv('MSG_HANDLING_CONCURRENCY', '20'))
INACTIVITY_SLEEP_DELAY = int(getenv('INACTIVITY_SLEEP_DELAY', '60'))

class HackyMiddleware(BaseMiddleware):
    """A cool hacky way to keep instance active using webhooks but using polling for message handling.
        
        As it is not possible to use webhooks with polling and webhooks gives incosistent results.
    """
    timer: Timer
    bot: Any
    bot_sleep_sem = asyncio.BoundedSemaphore()
    bot_activity_sem = asyncio.BoundedSemaphore(MSG_HANDLING_CONCURRENCY)
    timer_create_sem = asyncio.BoundedSemaphore()

    def __init__(self, tg_bot: Any):
        super(HackyMiddleware, self).__init__()
        self.bot = tg_bot
        
        logging.info('Inactivity sleep timer set to %d seconds', INACTIVITY_SLEEP_DELAY)
        logging.info('Message handling concurrency set to %d', MSG_HANDLING_CONCURRENCY)

    def __awake(self) -> bool:
        return self.bot.method == BotEventMethods.polling

    async def create_sleep_timer(self, delay: int = INACTIVITY_SLEEP_DELAY):
        while True:
            try:
                async with self.timer_create_sem:
                    # timer is scheduled here
                    self.timer = Timer(delay, callback=HackyMiddleware.goto_sleep, callback_args=[self])

                # wait until the callback has been executed
                await self.timer.wait()
            except asyncio.CancelledError:
                # get clock time
                logging.debug('Bot timer cancelled')
                pass

            if not self.__awake():
                break

    async def goto_sleep(self):
        async with self.bot_sleep_sem:
            if self.__awake():
                logging.info('Bot going to sleep...')
                await self.bot.stop_polling()
                await self.bot.set_webhook()

    async def wake_up(self):
        async with self.bot_sleep_sem:
            if not self.__awake():
                logging.info('Bot waking up...')
                await self.bot.delete_webhook()
                asyncio.create_task(self.bot.start_polling())
                asyncio.create_task(self.create_sleep_timer())

    async def startup(self):
        if not self.__awake():
            logging.debug('HackyMiddleware starting...')
            await self.wake_up()

    async def shutdown(self):
        if self.__awake():
            logging.debug('HackyMiddleware closing...')
            await self.goto_sleep()
            self.timer.cancel()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        try:
            # acquire lock to hold the sleep timer
            if self.bot_activity_sem._bound_value == self.bot_activity_sem._value:
                await self.timer_create_sem.acquire()
                self.timer.cancel()

            async with self.bot_activity_sem:
                if not self.__awake():
                    asyncio.create_task(self.wake_up())
                    return Response(status=400, text='Bot is asleep')
                else:
                    return await handler(event, data)
        finally:
            # release lock if there is no more activity
            if self.bot_activity_sem._bound_value == self.bot_activity_sem._value:
                self.timer_create_sem.release()
