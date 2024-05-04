from dependency_injector import providers, containers
from bot.bot import TgBot

from chat.memorizer import Memorizer
from chat.prompt_generator import PromptGenerator
from chat.services.db import DbService
from chat.services.img_gen import ImgGenService
from chat.query_processor import QueryProcessor
from chat.repository import ChatRepo
from chat.services.gemini import GeminiService
from chat.services.voice import VoiceService

class Configs(containers.DeclarativeContainer):
    bot_config = providers.Configuration('bot')
    chat_config = providers.Configuration('chat')

class BotContainer(containers.DeclarativeContainer):
    chat_service = providers.Singleton(GeminiService, api_key=Configs.chat_config.api_key)
    voice_service = providers.Singleton(VoiceService, voice_api_url=Configs.chat_config.voice_api_url, tts_voice=Configs.chat_config.tts_voice, stt_engine=Configs.chat_config.stt_engine)
    img_service = providers.Singleton(ImgGenService, bing_cookie=Configs.chat_config.bing_cookie, google_cookie=Configs.chat_config.google_cookie)
    db_service = providers.Singleton(DbService, url=Configs.chat_config.mongo_db_url)
    memorizer = providers.Singleton(Memorizer, db=db_service, gemini=chat_service)
    query_processor = providers.Singleton(QueryProcessor, gemini=chat_service, voice=voice_service, img_gen=img_service)
    prompt_generator = providers.Singleton(PromptGenerator, voice_service=voice_service, memorizer=memorizer)
    chat_repo = providers.Factory(ChatRepo, gemini=chat_service, processor=query_processor, generator=prompt_generator, db=db_service, memorizer=memorizer)
    tg_bot = providers.Singleton(TgBot, token=Configs.bot_config.token, chat_repo=chat_repo, webhook_host=Configs.bot_config.webhook_host, webhook_secret=Configs.bot_config.webhook_secret)
