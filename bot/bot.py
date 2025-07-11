from logging import Logger, getLogger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp.web import Application
from httpx import URL

from bot.routers import commands, prompts
from bot.middlewares.wake_me_up import WakeMeUpMiddleware
from common.types.enums import BotEventMethods
from chat.repository import ChatRepo
from chat.services.voice import VoiceService

logging: Logger = getLogger(__name__)

class TgBot(object):
    bot: Bot
    dispatcher: Dispatcher
    chat_repo: ChatRepo
    voice_service: VoiceService
    webhook_host: str
    webhook_path: str
    secret: str
    method: BotEventMethods

    routers = [
        commands.command_router,
        prompts.prompts_router
    ]

    def __setup_wake_me_up__(self):
        hacky = WakeMeUpMiddleware(self)
        self.dispatcher.message.middleware.register(hacky)
        self.dispatcher.startup.register(hacky.startup)
        self.dispatcher.shutdown.register(hacky.shutdown)

    def __init__(self, token: str, chat_repo: ChatRepo, voice_service: VoiceService, webhook_host: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2, webhook_secret: str = ''):
        self.bot = Bot(token, default=DefaultBotProperties(parse_mode=parse_mode))
        self.dispatcher = Dispatcher()
        self.dispatcher.include_routers(*self.routers)
        self.chat_repo = chat_repo
        self.voice_service = voice_service
        self.webhook_host = webhook_host
        self.secret = webhook_secret
        self.method = BotEventMethods.unknown
        self.__setup_wake_me_up__()

    def register_webhook_handler(self, app: Application, path: str):
        # Create an instance of request handler,
        # aiogram has few implementations for different cases of usage
        # In this example we use SimpleRequestHandler which is designed to handle simple cases
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=self.dispatcher,
            bot=self.bot,
            secret_token=self.secret,
            repo=self.chat_repo,
            handle_in_background=False
        )
        # Register webhook handler on application
        webhook_requests_handler.register(app, path=path)

        # Mount dispatcher startup and shutdown hooks to aiohttp application
        setup_application(app, self.dispatcher, bot=self.bot)

        self.webhook_path = path

    async def set_webhook(self, drop_pending_updates = False):
        if not self.webhook_host or self.webhook_host.strip() == '':
            # No webhook url set
            logging.warning('env APP_HOSTNAME is not set...')
            return False
        
        webhook_url = URL(f'https://{self.webhook_host}').join(self.webhook_path)
        logging.debug(f'Bot webhook set to {webhook_url}...')
        webhook_info = await self.bot.get_webhook_info()
        self.method = BotEventMethods.webhook

        if webhook_info.url != webhook_url or drop_pending_updates:
            return await self.bot.set_webhook(url=str(webhook_url), secret_token=self.secret, drop_pending_updates=drop_pending_updates)
        return True

    def delete_webhook(self, drop_pending_updates = False):
        logging.debug('Bot webhook deleted...')
        self.method = BotEventMethods.unknown
        return self.bot.delete_webhook(drop_pending_updates=drop_pending_updates)
    
    def start_polling(self):
        self.method = BotEventMethods.polling
        return self.dispatcher.start_polling(self.bot, handle_signals=False, repo=self.chat_repo, voice_service=self.voice_service)
    
    def stop_polling(self):
        self.method = BotEventMethods.unknown
        return self.dispatcher.stop_polling()
