from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.core.memory import UserMemory, AgentMemory
from app.core.agent import MemoryExtractor
from app.config import settings

router = APIRouter()

class MemoryRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    auto_extract: bool = False  # 是否自动抽取

class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

user_memory = UserMemory() if settings.ENABLE_USER_MEMORY else None
agent_memory = AgentMemory() if settings.ENABLE_AGENT_MEMORY else None
memory_extractor = MemoryExtractor()

@router.post("/memory/user/{user_id}")
async def store_user_memory(user_id: str, request: MemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    if request.auto_extract:
        # 自动抽取模式（包含去重和更新判断）
        # 先获取现有记忆作为上下文
        existing = await user_memory.query(user_id, "recent memories", top_k=50)
        existing_memories = [
            {"id": m.id, "content": m.content, "metadata": m.meta_info}
            for m in existing
        ]
        
        # 抽取新记忆
        memories = await memory_extractor.extract_memories(
            request.content, 
            user_id, 
            existing_memories
        )
        
        # 根据操作类型处理记忆
        results = {
            "mode": "auto_extract",
            "total_extracted": len(memories),
            "inserted": 0,
            "updated": 0,
            "ignored": 0,
            "memories": []
        }
        
        for mem in memories:
            action = mem.get("action", "insert")
            
            if action == "ignore":
                # 忽略重复记忆
                results["ignored"] += 1
                continue
            elif action == "update":
                # 更新现有记忆
                if "memory_id" in mem:
                    updated = await user_memory.update(
                        mem["memory_id"],
                        mem.get("content"),
                        mem.get("metadata")
                    )
                    if updated:
                        results["updated"] += 1
                        results["memories"].append({
                            "id": updated.id,
                            "action": "update",
                            "status": "success",
                            "updated_at": updated.updated_at
                        })
            else:  # insert
                # 插入新记忆
                memory = await user_memory.store(
                    user_id, 
                    mem["content"], 
                    mem.get("metadata")
                )
                results["inserted"] += 1
                results["memories"].append({
                    "id": memory.id,
                    "action": "insert",
                    "status": "success",
                    "created_at": memory.created_at
                })
        
        return results
    else:
        # 直接存储模式
        memory = await user_memory.store(user_id, request.content, request.metadata)
        return {"id": memory.id, "status": "success", "created_at": memory.created_at, "mode": "direct"}

@router.post("/memory/agent/{agent_id}")
async def store_agent_memory(agent_id: str, request: MemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    if request.auto_extract:
        # 自动抽取模式（包含去重和更新判断）
        # 先获取现有记忆作为上下文
        existing = await agent_memory.query(agent_id, "recent memories", top_k=50)
        existing_memories = [
            {"id": m.id, "content": m.content, "metadata": m.meta_info}
            for m in existing
        ]
        
        # 抽取新记忆
        memories = await memory_extractor.extract_memories(
            request.content, 
            agent_id, 
            existing_memories
        )
        
        # 根据操作类型处理记忆
        results = {
            "mode": "auto_extract",
            "total_extracted": len(memories),
            "inserted": 0,
            "updated": 0,
            "ignored": 0,
            "memories": []
        }
        
        for mem in memories:
            action = mem.get("action", "insert")
            
            if action == "ignore":
                # 忽略重复记忆
                results["ignored"] += 1
                continue
            elif action == "update":
                # 更新现有记忆
                if "memory_id" in mem:
                    updated = await agent_memory.update(
                        mem["memory_id"],
                        mem.get("content"),
                        mem.get("metadata")
                    )
                    if updated:
                        results["updated"] += 1
                        results["memories"].append({
                            "id": updated.id,
                            "action": "update",
                            "status": "success",
                            "updated_at": updated.updated_at
                        })
            else:  # insert
                # 插入新记忆
                memory = await agent_memory.store(
                    agent_id, 
                    mem["content"], 
                    mem.get("metadata")
                )
                results["inserted"] += 1
                results["memories"].append({
                    "id": memory.id,
                    "action": "insert",
                    "status": "success",
                    "created_at": memory.created_at
                })
        
        return results
    else:
        # 直接存储模式
        memory = await agent_memory.store(agent_id, request.content, request.metadata)
        return {"id": memory.id, "status": "success", "created_at": memory.created_at, "mode": "direct"}

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
