import asyncio
import logging
import aiohttp
from aiogram.types import InputMediaPhoto, BufferedInputFile
from duckduckgo_search import AsyncDDGS
from google.generativeai.generative_models import ChatSession, content_types

from chat.service import ChatService
from prompts.keywords import IMAGE_QUERY, SEARCH_QUERIES
from prompts.templates import build_searchengine_response_prompt

class QueryProcessor():
    __service: ChatService

    def __init__(self, service: ChatService):
        self.__service = service

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
    
    async def __download_image__(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    file_format = response.headers.get('content-type').split('/')[-1]
                    # svg is not supported
                    if file_format.__contains__('svg'):
                        raise Exception(f"Url: {url}, unsupported format: {file_format}")
                    else:
                        image_bytes = await response.read()
                        file_name = f"{url.split('/')[-1]}.{file_format}"
                        return (file_name, image_bytes)
                else:
                    raise Exception(f"Url: {url}, status code: {response.status}")
    
    async def __fetch_images_from_url__(self, urls: list[str]):
        tasks: list[asyncio.Task[tuple[str, bytes]]] = []
        images: list[InputMediaPhoto] = []

        
        for url in urls:
            task = asyncio.create_task(self.__download_image__(url))
            tasks.append(task)

        for task in asyncio.as_completed(tasks):
            try:
                filename, filebytes = await task
                images.append(InputMediaPhoto(media=BufferedInputFile(filebytes, filename=filename)))
            except Exception as e:
                logging.warning(f"Failed to download image: {str(e)}")
        
        return images
    
    async def process_response(self, session: ChatSession, messages: list[content_types.PartType]):
        text = ""
        has_query = False
        response_stream = self.__service.gen_response_stream(prompts=messages, chat=session)

        async for res in response_stream:
            text += res
            if len(text) > 15:
                if text.startswith(f"{SEARCH_QUERIES}:") or text.startswith(f"{IMAGE_QUERY}:"):
                    has_query = True
                else:
                    yield text
                    text = ""

        if len(text) > 0 and not has_query:
            yield text

        if has_query:
            if text.startswith(f"{IMAGE_QUERY}:"):
                query = text.replace(f"{IMAGE_QUERY}:", "").strip()
                image_urls = await self.__service.gen_image_response(query)
                yield await self.__fetch_images_from_url__(image_urls)
            else:
                queries = text.replace(f"{SEARCH_QUERIES}:\n-", "").split("\n-")
                query_responses_prompt = await self.__gen_live_data_prompt__(queries)
                response_stream = self.process_response(session=session, messages=[query_responses_prompt])
                async for res in response_stream:
                    yield res
