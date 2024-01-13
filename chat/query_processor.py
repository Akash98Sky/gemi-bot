import asyncio
from logging import Logger, getLogger
import pyttsx3
from aiogram.types import InputMediaPhoto, InputMediaAudio, FSInputFile
from duckduckgo_search import AsyncDDGS
from google.generativeai.generative_models import ChatSession, content_types
import time

from chat.service import ChatService
from prompts.keywords import IMAGE_QUERY, SEARCH_QUERIES, VOICE_RESPONSE
from prompts.templates import build_searchengine_response_prompt

logging: Logger = getLogger(__name__)

class QueryProcessor():
    __service: ChatService
    __voice_engine: pyttsx3.Engine
    __query_list__ = [
        IMAGE_QUERY,
        SEARCH_QUERIES,
        VOICE_RESPONSE
    ]

    def __init__(self, service: ChatService):
        self.__service = service
        self.__voice_engine = pyttsx3.init()
        self.__voice_engine.setProperty('voice', 'mb-us1')
        self.__voice_engine.setProperty('rate', 100)

    async def __process_searchengine_query__(self, query: str):
        async with AsyncDDGS() as ddgs:
            async for res in ddgs.text(query, region="in-en", max_results=1):
                res['query'] = query
                return res

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
        image_urls: list[str] | None = await self.__service.gen_image_response(query)
        images: list[InputMediaPhoto] = []

        if image_urls:
            logging.debug(f"Image URLs: {image_urls}")
            images = [InputMediaPhoto(media=url) for url in image_urls if not url.endswith('svg')]  # ignore svg format image urls
        
        return images
    
    async def __gen_voice_data__(self, query: str, chat_id: int):
        logging.debug(f"Generate voice query: {query}")
        file_path = f"temp/voice_{chat_id}_{int(time.time())}.mp3"
        self.__voice_engine.save_to_file(query, file_path)
        self.__voice_engine.runAndWait()
        return InputMediaAudio(media=FSInputFile(file_path))
    
    async def process_response(self, session: ChatSession, messages: list[content_types.PartType], chat_id: int):
        text = ""
        has_query = False
        response_stream = self.__service.gen_response_stream(prompts=messages, chat=session)

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
