
import asyncio
import logging
from typing import Any, AsyncGenerator, Callable
from duckduckgo_search import AsyncDDGS

from prompts.templates import build_searchengine_response_prompt

class QueryProcessor():
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
    
    async def intercepted_response(self, res: AsyncGenerator[str, Any], on_query_cb: Callable[[str], AsyncGenerator[str, Any]]):
        text = ""
        has_query = False
        async for r in res:
            text += r
            if has_query:
                pass
            elif len(r) >= 22:
                if text.startswith("search_queries:"):
                    has_query = True
                else:
                    yield text
                    text = ""

        if has_query:
            queries = text.split("\n-")
            query_responses_prompt = await self.__gen_live_data_prompt__(queries)
            async for r in on_query_cb(query_responses_prompt):
                yield r
            

