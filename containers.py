from dependency_injector import providers, containers
from bot.bot import TgBot
from chat.query_processor import QueryProcessor
from chat.repository import ChatRepo
from chat.service import ChatService
from chat.voice_engine import VoiceEngine

class Configs(containers.DeclarativeContainer):
    bot_config = providers.Configuration('bot')
    chat_config = providers.Configuration('chat')

class BotContainer(containers.DeclarativeContainer):
    chat_service = providers.Singleton(ChatService, api_key=Configs.chat_config.api_key, bing_cookie=Configs.chat_config.bing_cookie)
    voice_engine = providers.Singleton(VoiceEngine, voice_api_url=Configs.chat_config.voice_api_url, tts_voice=Configs.chat_config.tts_voice)
    query_processor = providers.Singleton(QueryProcessor, service=chat_service, voice=voice_engine)
    chat_repo = providers.Factory(ChatRepo, service=chat_service, processor=query_processor)
    tg_bot = providers.Singleton(TgBot, token=Configs.bot_config.token, chat_repo=chat_repo, webhook_host=Configs.bot_config.webhook_host, webhook_secret=Configs.bot_config.webhook_secret)
