from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.memory import UserMemory, AgentMemory
from app.config import settings

router = APIRouter()

class MemoryRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

user_memory = UserMemory() if settings.ENABLE_USER_MEMORY else None
agent_memory = AgentMemory() if settings.ENABLE_AGENT_MEMORY else None

@router.post("/memory/user/{user_id}")
async def store_user_memory(user_id: str, request: MemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    memory = await user_memory.store(user_id, request.content, request.metadata)
    return {"id": memory.id, "status": "success", "created_at": memory.created_at}

@router.post("/memory/agent/{agent_id}")
async def store_agent_memory(agent_id: str, request: MemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    memory = await agent_memory.store(agent_id, request.content, request.metadata)
    return {"id": memory.id, "status": "success", "created_at": memory.created_at}

@router.put("/memory/user/{user_id}/{memory_id}")
async def update_user_memory(user_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    memory = await user_memory.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    if memory.entity_id != user_id:
        raise HTTPException(status_code=403, detail="Memory does not belong to this user")
    
    updated = await user_memory.update(memory_id, request.content, request.metadata)
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "id": updated.id,
        "status": "success",
        "updated_at": updated.updated_at,
        "content": updated.content,
        "metadata": updated.meta_info
    }

@router.put("/memory/agent/{agent_id}/{memory_id}")
async def update_agent_memory(agent_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    memory = await user_memory.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    if memory.entity_id != agent_id:
        raise HTTPException(status_code=403, detail="Memory does not belong to this agent")
    
    updated = await agent_memory.update(memory_id, request.content, request.metadata)
    if not updated:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {
        "id": updated.id,
        "status": "success",
        "updated_at": updated.updated_at,
        "content": updated.content,
        "metadata": updated.meta_info
    }

@router.delete("/memory/user/{user_id}/{memory_id}")
async def delete_user_memory(user_id: str, memory_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    memory = await user_memory.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    if memory.entity_id != user_id:
        raise HTTPException(status_code=403, detail="Memory does not belong to this user")
    
    success = await user_memory.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"id": memory_id, "status": "success", "message": "Memory deleted successfully"}

@router.delete("/memory/agent/{agent_id}/{memory_id}")
async def delete_agent_memory(agent_id: str, memory_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    memory = await user_memory.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    if memory.entity_id != agent_id:
        raise HTTPException(status_code=403, detail="Memory does not belong to this agent")
    
    success = await agent_memory.delete(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"id": memory_id, "status": "success", "message": "Memory deleted successfully"}

@router.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=403, detail="User memory is not enabled")
    
    memory = await user_memory.get_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {
        "id": memory.id,
        "content": memory.content,
        "metadata": memory.meta_info,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at
    }
