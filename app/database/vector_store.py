from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct
from typing import List, Dict, Any, Optional
from app.config import settings
import uuid

class QdrantStore:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        if settings.EMBEDDING_PROVIDER == "dashscope":
            self.embedding_dim = settings.DASHSCOPE_EMBEDDING_DIM
        else:
            self.embedding_dim = settings.OPENAI_EMBEDDING_DIM

    def _get_collection_name(self, memory_type: str, entity_id: str) -> str:
        return f"{settings.QDRANT_COLLECTION_PREFIX}_{memory_type}_{entity_id}"

    def ensure_collection(self, collection_name: str):
        collections = self.client.get_collections()
        existing = [c.name for c in collections.collections]
        
        if collection_name not in existing:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE)
            )

    async def insert(self, memory_id: str, embedding: List[float], 
                    memory_type: str, entity_id: str, metadata: Dict[str, Any] = None):
        collection_name = self._get_collection_name(memory_type, entity_id)
        self.ensure_collection(collection_name)
        
        # Use UUID as point ID, store original memory_id in payload
        point_uuid = uuid.uuid4()
        point = PointStruct(
            id=point_uuid,
            vector=embedding,
            payload={"memory_id": memory_id, **(metadata or {})}
        )
        self.client.upsert(collection_name=collection_name, points=[point])
        
        return point_uuid

    async def search(self, query_embedding: List[float], memory_type: str, 
                    entity_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        collection_name = self._get_collection_name(memory_type, entity_id)
        
        response = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )

        return [
            {
                "memory_id": point.payload.get("memory_id", str(point.id)),
                "score": point.score,
                "payload": point.payload
            }
            for point in response
        ]

    async def update(self, memory_id: str, embedding: Optional[List[float]], 
                    memory_type: str, entity_id: str, metadata: Dict[str, Any] = None):
        collection_name = self._get_collection_name(memory_type, entity_id)
        
        payload = {"memory_id": memory_id}
        if metadata:
            payload.update(metadata)
        
        point = {
            "id": memory_id,
            "vector": embedding,
            "payload": payload
        }
        self.client.upsert(collection_name=collection_name, points=[point])

    async def delete(self, memory_id: str, memory_type: str, entity_id: str):
        collection_name = self._get_collection_name(memory_type, entity_id)
        self.client.delete(
            collection_name=collection_name,
            points_selector=[memory_id]
        )
