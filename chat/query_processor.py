
import asyncio
import logging
from duckduckgo_search import AsyncDDGS
from google.generativeai.generative_models import ChatSession, content_types

from chat.service import ChatService
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
    
    async def process_response(self, session: ChatSession, messages: list[content_types.PartType]):
        text = ""
        has_query = False
        response_stream = self.__service.gen_response_stream(prompts=messages, chat=session)
        async for res in response_stream:
            text += res
            if has_query:
                pass
            elif len(text) >= 22:
                if text.startswith("search_queries:"):
                    has_query = True
                else:
                    yield text
                    text = ""

        if has_query:
            queries = text.replace("search_queries:\n-", "").split("\n-")
            query_responses_prompt = await self.__gen_live_data_prompt__(queries)
            response_stream = self.__service.gen_response_stream(prompts=[query_responses_prompt], chat=session)
            async for res in response_stream:
                yield res
