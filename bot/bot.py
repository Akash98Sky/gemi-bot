from logging import Logger, getLogger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp.web import Application

from bot.routes import routers
from bot.hack import HackyMiddleware
from bot.enums import BotEventMethods
from chat.repository import ChatRepo
from chat.voice_engine import VoiceEngine

logging: Logger = getLogger(__name__)

class TgBot(object):
    bot: Bot
    dispatcher: Dispatcher
    chat_repo: ChatRepo
    voice_engine: VoiceEngine
    webhook_host: str
    webhook_path: str
    secret: str
    method: BotEventMethods

    routers = routers

    def __something_hacky__(self):
        hacky = HackyMiddleware(self)
        self.dispatcher.message.middleware.register(hacky)
        self.dispatcher.startup.register(hacky.startup)
        self.dispatcher.shutdown.register(hacky.shutdown)

    def __init__(self, token: str, chat_repo: ChatRepo, voice_engine: VoiceEngine, webhook_host: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2, webhook_secret: str = ''):
        self.bot = Bot(token, parse_mode=parse_mode)
        self.dispatcher = Dispatcher()
        self.dispatcher.include_routers(*self.routers)
        self.chat_repo = chat_repo
        self.voice_engine = voice_engine
        self.webhook_host = webhook_host
        self.secret = webhook_secret
        self.method = BotEventMethods.unknown
        self.__something_hacky__()

    def start_polling(self):
        self.method = BotEventMethods.polling
        return self.dispatcher.start_polling(self.bot, handle_signals=False, repo=self.chat_repo, voice_engine=self.voice_engine)
    
    def register_webhook_handler(self, app: Application, path: str):
        # Create an instance of request handler,
        # aiogram has few implementations for different cases of usage
        # In this example we use SimpleRequestHandler which is designed to handle simple cases
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=self.dispatcher,
            bot=self.bot,
            secret_token=self.secret,
            repo=self.chat_repo,
            voice_engine=self.voice_engine,
            handle_in_background=False
        )
        # Register webhook handler on application
        webhook_requests_handler.register(app, path=path)

        # Mount dispatcher startup and shutdown hooks to aiohttp application
        setup_application(app, self.dispatcher, bot=self.bot)

        self.webhook_path = path

    async def set_webhook(self, drop_pending_updates = False):
        webhook_url = f'https://{self.webhook_host}{self.webhook_path}'
        logging.debug(f'Bot webhook set to {webhook_url}...')
        webhook_info = await self.bot.get_webhook_info()
        self.method = BotEventMethods.webhook

        if webhook_info.url != webhook_url or drop_pending_updates:
            # Drop pending updates so that it does not keep retrying
            # No need to wait longer than 20 secsonds
            return await self.bot.set_webhook(url=webhook_url, secret_token=self.secret, drop_pending_updates=drop_pending_updates)
        return True

    def delete_webhook(self, drop_pending_updates = False):
        logging.debug('Bot webhook deleted...')
        self.method = BotEventMethods.unknown
        return self.bot.delete_webhook(drop_pending_updates=drop_pending_updates)
    
    def stop_polling(self):
        self.method = BotEventMethods.unknown
        return self.dispatcher.stop_polling()
    
    def close(self):
        return self.bot.close()
