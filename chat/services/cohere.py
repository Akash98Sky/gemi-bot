from logging import getLogger, Logger
import cohere

logging: Logger = getLogger(__name__)

class CohereService:
    def __init__(self, api_key: str):
        self.client = cohere.AsyncClient(api_key)

    async def embed_texts(self, texts: list[str]):
        res = await self.client.embed(texts=texts, input_type='search_document', model='embed-multilingual-v3.0')

        return res.embeddings
    
    async def embed_query(self, query: str):
        res = await self.client.embed(texts=[query], input_type='search_query', model='embed-multilingual-v3.0')

        return list[float](res.embeddings[0]) if len(res.embeddings) > 0 else None