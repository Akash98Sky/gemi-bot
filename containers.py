from dependency_injector import providers, containers
from bot.bot import TgBot
from chat.service import ChatService

class Configs(containers.DeclarativeContainer):
    bot_config = providers.Configuration('bot')
    chat_config = providers.Configuration('chat')

class BotContainer(containers.DeclarativeContainer):
    chat_service = providers.Singleton(ChatService, api_key=Configs.chat_config.api_key)
    tg_bot = providers.Singleton(TgBot, token=Configs.bot_config.token, service=chat_service)
