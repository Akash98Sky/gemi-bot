import asyncio
from logging import Logger, getLogger
from aiogram.types import InputMediaPhoto, InputMediaAudio, URLInputFile
from duckduckgo_search import AsyncDDGS
from google.generativeai.generative_models import ChatSession, content_types
import time

from chat.services.gemini import GeminiService
from chat.services.voice import VoiceService
from chat.services.img_gen import ImgGenService
from common.constants.keywords import IMAGE_QUERY, SEARCH_QUERIES, VOICE_RESPONSE
from chat.prompts.templates import build_searchengine_response_prompt

logging: Logger = getLogger(__name__)

class QueryProcessor():
    __gemini: GeminiService
    __voice: VoiceService
    __img_gen: ImgGenService
    __query_list__ = [
        IMAGE_QUERY,
        SEARCH_QUERIES,
        VOICE_RESPONSE
    ]

    def __init__(self, gemini: GeminiService, voice: VoiceService, img_gen: ImgGenService):
        self.__gemini = gemini
        self.__voice = voice
        self.__img_gen = img_gen

    async def __process_searchengine_query__(self, query: str):
        async with AsyncDDGS() as ddgs:
            res = await ddgs.text(query, region="in-en", max_results=1)
            res[0]['query'] = query
            return res[0]

    async def __gen_live_data_prompt__(self, queries: list[str]):
        logging.debug(f"Generating live data prompt for queries: {queries}")
        query_responses: list[dict[str, str]] = []
        tasks: list[asyncio.Task] = [
            asyncio.create_task(self.__process_searchengine_query__(query.strip())) for query in queries
        ]

        for task in tasks:
            task.add_done_callback(lambda res: query_responses.append(res.result()))
        await asyncio.gather(*tasks)

        logging.debug(f"Query responses: {query_responses}")
        return build_searchengine_response_prompt(query_responses)
    
    async def __gen_image_data__(self, query: str):
        logging.debug(f"Generate image query: {query}")
        image_urls: list[str] | None = await self.__img_gen.gen_image_response(query)
        images: list[InputMediaPhoto] = []

        if image_urls:
            logging.debug(f"Image URLs: {image_urls}")
            images = [InputMediaPhoto(media=url) for url in image_urls if not url.endswith('svg')]  # ignore svg format image urls
        
        return images
    
    async def __gen_voice_data__(self, query: str, chat_id: int):
        logging.debug(f"Generate voice query: {query}")
        file_name = f"voice_{chat_id}_{int(time.time())}.wav"
        text_voice_url = await self.__voice.text_to_wave(query)
        if text_voice_url:
            return InputMediaAudio(media=URLInputFile(text_voice_url, filename=file_name))
    
    async def process_response(self, session: ChatSession, messages: list[content_types.PartType], chat_id: int):
        text = ""
        has_query = False
        response_stream = self.__gemini.gen_response_stream(prompts=messages, chat=session)

        async for res in response_stream:
            text += res
            if len(text) > 15:
                if len([query for query in self.__query_list__ if text.startswith(f"{query}:")]) > 0:
                    has_query = True
                else:
                    yield text
                    text = ""

        if len(text) > 0 and not has_query:
            yield text

        if has_query:
            if text.startswith(f"{IMAGE_QUERY}:"):
                query = text.replace(f"{IMAGE_QUERY}:", "").strip()
                yield await self.__gen_image_data__(query)
            elif text.startswith(f"{VOICE_RESPONSE}:"):
                query = text.replace(f"{VOICE_RESPONSE}:", "").strip()
                yield await self.__gen_voice_data__(query, chat_id)
            else:
                queries = text.replace(f"{SEARCH_QUERIES}:\n-", "").split("\n-")
                query_responses_prompt = await self.__gen_live_data_prompt__(queries)
                response_stream = self.process_response(session=session, messages=[query_responses_prompt], chat_id=chat_id)
                async for res in response_stream:
                    yield res
