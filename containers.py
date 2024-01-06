from dependency_injector import providers, containers
from bot.bot import TgBot
from chat.repository import ChatRepo
from chat.service import ChatService

class Configs(containers.DeclarativeContainer):
    bot_config = providers.Configuration('bot')
    chat_config = providers.Configuration('chat')

class BotContainer(containers.DeclarativeContainer):
    chat_service = providers.Singleton(ChatService, api_key=Configs.chat_config.api_key, bing_cookie=Configs.chat_config.bing_cookie)
    chat_repo = providers.Factory(ChatRepo, service=chat_service)
    tg_bot = providers.Singleton(TgBot, token=Configs.bot_config.token, chat_repo=chat_repo, webhook_host=Configs.bot_config.webhook_host, webhook_secret=Configs.bot_config.webhook_secret)
