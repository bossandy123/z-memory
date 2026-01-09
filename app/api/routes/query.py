from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.memory import UserMemory, AgentMemory
from app.core.decision import DecisionLayer
from app.config import settings

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    top_k: int = 5

user_memory = UserMemory() if settings.ENABLE_USER_MEMORY else None
agent_memory = AgentMemory() if settings.ENABLE_AGENT_MEMORY else None
decision_layer = DecisionLayer(user_memory, agent_memory) if user_memory or agent_memory else None

@router.post("/memory/query")
async def query_memory(request: QueryRequest):
    if not decision_layer:
        raise HTTPException(status_code=503, detail="No memory modules enabled")
    
    if not request.user_id and not request.agent_id:
        raise HTTPException(status_code=400, detail="Either user_id or agent_id is required")
    
    if request.user_id and not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=400, detail="User memory is not enabled")
    
    if request.agent_id and not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=400, detail="Agent memory is not enabled")
    
    results = await decision_layer.query(
        request.query, 
        request.user_id, 
        request.agent_id, 
        request.top_k
    )
    
    return {
        "query": request.query,
        "results": results
    }
