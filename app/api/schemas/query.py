from pydantic import BaseModel
from typing import Optional, Dict, Any


class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    top_k: int = 5


class MemoryResult(BaseModel):
    id: str
    entity_id: str
    entity_type: str
    memory_layer: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    score: float


class QueryResponse(BaseModel):
    query: str
    total_results: int
    user_memories: list[MemoryResult]
    agent_memories: list[MemoryResult]
