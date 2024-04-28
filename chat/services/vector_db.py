from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class VectorDbService:
    client: QdrantClient
    collection_name: str

    def __init__(self, url: str, api_key: str, collection_name: str = "test_collection"):
        self.client = QdrantClient(
            url=url,
            port=6333,
            api_key=api_key
        )
        self.collection_name = collection_name
        self.__init_collection()

    def __init_collection(self):
        collections = self.client.get_collections().collections
        if self.collection_name not in [collection.name for collection in collections]:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def add_vectors(self, points: list[PointStruct]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

