from logging import Logger, getLogger
from typing import Literal
from tavily import AsyncTavilyClient


logging: Logger = getLogger(__name__)

class TavilyService:
    client: AsyncTavilyClient

    def __init__(self, api_key: str):
        self.client = AsyncTavilyClient(api_key=api_key)

    async def search(self, query: str, max_results: int = 1, topic: Literal['general', 'news'] = 'general'):
        logging.debug(f"Tavily search query: {query}")
        return await self.client.search(
            query=query,
            topic=topic,
            max_results=max_results,
            include_answer=True
        )