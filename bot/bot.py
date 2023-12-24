from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.routes import router
from chat.service import ChatService

class TgBot(object):
    bot: Bot
    dispatcher: Dispatcher
    service: ChatService

    routers = [ router ]

    def __init__(self, token: str, service: ChatService, parse_mode: ParseMode = ParseMode.MARKDOWN):
        self.bot = Bot(token, parse_mode=parse_mode)
        self.dispatcher = Dispatcher()
        self.dispatcher.include_routers(*self.routers)
        self.service = service

    def start_polling(self):
        return self.dispatcher.start_polling(self.bot, chat=self.service)
    
    def stop_polling(self):
        return self.dispatcher.stop_polling()
