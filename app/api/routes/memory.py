from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.core.memory import UserMemory, AgentMemory, MemoryLogger
from app.core.agent import MemoryExtractor
from app.config import settings
from app.database.models import ProfileMemory, EventMemory, MemoryLog

router = APIRouter()

class MemoryRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    auto_extract: bool = False  # 是否自动抽取
    memory_layer: Optional[str] = None  # 'profile' or 'event'
    is_permanent: bool = False

class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None  # 更新原因（自然语言）

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
        existing_profiles = await user_memory.get_profile(user_id)
        existing_events = await user_memory.get_events(user_id, limit=50)
        
        existing_memories = [
            {"id": m.id, "content": m.content, "metadata": m.meta_info, 
             "memory_layer": "profile"}
            for m in existing_profiles
        ] + [
            {"id": m.id, "content": m.content, "metadata": m.meta_info,
             "memory_layer": "event"}
            for m in existing_events
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
            "profile_count": 0,
            "event_count": 0,
            "memories": []
        }
        
        for mem in memories:
            action = mem.get("action", "insert")
            layer = mem.get("memory_layer", "event")
            
            if layer == "profile":
                results["profile_count"] += 1
            else:
                results["event_count"] += 1
            
            if action == "ignore":
                # 忽略重复记忆，记录日志
                results["ignored"] += 1
                if "memory_id" in mem:
                    await MemoryLogger.log_action(
                        mem["memory_id"],
                        layer,
                        "ignore",
                        mem.get("reason", ""),
                        {"layer": layer, "content": mem.get("content", "")}
                    )
                results["memories"].append({
                    "id": mem.get("memory_id", ""),
                    "action": "ignore",
                    "layer": layer,
                    "reason": mem.get("reason", ""),
                    "status": "success"
                })
            elif action == "update":
                # 更新现有记忆
                if "memory_id" in mem:
                    if layer == "profile":
                        updated = await user_memory.update_profile(
                            mem["memory_id"],
                            mem.get("content"),
                            mem.get("metadata"),
                            mem.get("reason", "")
                        )
                    else:
                        updated = await user_memory.update_event(
                            mem["memory_id"],
                            mem.get("content"),
                            mem.get("metadata"),
                            mem.get("reason", "")
                        )
                    if updated:
                        results["updated"] += 1
                        results["memories"].append({
                            "id": updated.id,
                            "action": "update",
                            "layer": layer,
                            "reason": mem.get("reason", ""),
                            "status": "success",
                            "updated_at": updated.updated_at
                        })
            else:  # insert
                # 插入新记忆
                if layer == "profile":
                    memory = await user_memory.store_profile(
                        user_id, 
                        mem["content"], 
                        mem.get("metadata")
                    )
                else:
                    memory = await user_memory.store_event(
                        user_id, 
                        mem["content"], 
                        mem.get("metadata"),
                        mem.get("metadata", {}).get("is_permanent", False),
                        mem.get("metadata", {}).get("expiry_date")
                    )
                results["inserted"] += 1
                results["memories"].append({
                    "id": memory.id,
                    "action": "insert",
                    "layer": layer,
                    "status": "success",
                    "created_at": memory.created_at
                })
        
        return results
    else:
        # 直接存储模式
        if request.memory_layer == "profile":
            memory = await user_memory.store_profile(
                user_id, 
                request.content, 
                request.metadata
            )
        else:
            memory = await user_memory.store_event(
                user_id, 
                request.content, 
                request.metadata,
                request.is_permanent
            )
        return {
            "id": memory.id, 
            "status": "success", 
            "created_at": memory.created_at,
            "mode": "direct",
            "layer": request.memory_layer or "event"
        }

@router.post("/memory/agent/{agent_id}")
async def store_agent_memory(agent_id: str, request: MemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    if request.auto_extract:
        # 自动抽取模式（包含去重和更新判断）
        # 先获取现有记忆作为上下文
        existing_profiles = await agent_memory.get_profile(agent_id)
        existing_events = await agent_memory.get_events(agent_id, limit=50)
        
        existing_memories = [
            {"id": m.id, "content": m.content, "metadata": m.meta_info,
             "memory_layer": "profile"}
            for m in existing_profiles
        ] + [
            {"id": m.id, "content": m.content, "metadata": m.meta_info,
             "memory_layer": "event"}
            for m in existing_events
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
            "profile_count": 0,
            "event_count": 0,
            "memories": []
        }
        
        for mem in memories:
            action = mem.get("action", "insert")
            layer = mem.get("memory_layer", "event")
            
            if layer == "profile":
                results["profile_count"] += 1
            else:
                results["event_count"] += 1
            
            if action == "ignore":
                # 忽略重复记忆，记录日志
                results["ignored"] += 1
                if "memory_id" in mem:
                    await MemoryLogger.log_action(
                        mem["memory_id"],
                        layer,
                        "ignore",
                        mem.get("reason", ""),
                        {"layer": layer, "content": mem.get("content", "")}
                    )
                results["memories"].append({
                    "id": mem.get("memory_id", ""),
                    "action": "ignore",
                    "layer": layer,
                    "reason": mem.get("reason", ""),
                    "status": "success"
                })
            elif action == "update":
                # 更新现有记忆
                if "memory_id" in mem:
                    if layer == "profile":
                        updated = await agent_memory.update_profile(
                            mem["memory_id"],
                            mem.get("content"),
                            mem.get("metadata"),
                            mem.get("reason", "")
                        )
                    else:
                        updated = await agent_memory.update_event(
                            mem["memory_id"],
                            mem.get("content"),
                            mem.get("metadata"),
                            mem.get("reason", "")
                        )
                    if updated:
                        results["updated"] += 1
                        results["memories"].append({
                            "id": updated.id,
                            "action": "update",
                            "layer": layer,
                            "reason": mem.get("reason", ""),
                            "status": "success",
                            "updated_at": updated.updated_at
                        })
            else:  # insert
                # 插入新记忆
                if layer == "profile":
                    memory = await agent_memory.store_profile(
                        agent_id, 
                        mem["content"], 
                        mem.get("metadata")
                    )
                else:
                    memory = await agent_memory.store_event(
                        agent_id, 
                        mem["content"], 
                        mem.get("metadata"),
                        mem.get("metadata", {}).get("is_permanent", False),
                        mem.get("metadata", {}).get("expiry_date")
                    )
                results["inserted"] += 1
                results["memories"].append({
                    "id": memory.id,
                    "action": "insert",
                    "layer": layer,
                    "status": "success",
                    "created_at": memory.created_at
                })
        
        return results
    else:
        # 直接存储模式
        if request.memory_layer == "profile":
            memory = await agent_memory.store_profile(
                agent_id, 
                request.content, 
                request.metadata
            )
        else:
            memory = await agent_memory.store_event(
                agent_id, 
                request.content, 
                request.metadata,
                request.is_permanent
            )
        return {
            "id": memory.id, 
            "status": "success", 
            "created_at": memory.created_at,
            "mode": "direct",
            "layer": request.memory_layer or "event"
        }

@router.get("/memory/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    profile = await user_memory.get_profile(user_id)
    return {
        "user_id": user_id,
        "layer": "profile",
        "count": len(profile),
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "metadata": m.meta_info,
                "updated_at": m.updated_at
            }
            for m in profile
        ]
    }

@router.get("/memory/user/{user_id}/events")
async def get_user_events(user_id: str, limit: int = 100):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    events = await user_memory.get_events(user_id, limit)
    return {
        "user_id": user_id,
        "layer": "event",
        "count": len(events),
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "metadata": m.meta_info,
                "created_at": m.created_at
            }
            for m in events
        ]
    }

@router.get("/memory/agent/{agent_id}/profile")
async def get_agent_profile(agent_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    profile = await agent_memory.get_profile(agent_id)
    return {
        "agent_id": agent_id,
        "layer": "profile",
        "count": len(profile),
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "metadata": m.meta_info,
                "updated_at": m.updated_at
            }
            for m in profile
        ]
    }

@router.get("/memory/agent/{agent_id}/events")
async def get_agent_events(agent_id: str, limit: int = 100):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    events = await agent_memory.get_events(agent_id, limit)
    return {
        "agent_id": agent_id,
        "layer": "event",
        "count": len(events),
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "metadata": m.meta_info,
                "created_at": m.created_at
            }
            for m in events
        ]
    }

@router.get("/memory/{memory_id}/logs")
async def get_memory_logs(memory_id: str, memory_layer: str, limit: int = 10):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    logs = await user_memory.get_logs(memory_id, memory_layer, limit)
    return {
        "memory_id": memory_id,
        "memory_layer": memory_layer,
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "action": log.action,
                "reason": log.reason,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }

@router.put("/memory/user/{user_id}/profile/{memory_id}")
async def update_user_profile(user_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    updated = await user_memory.update_profile(
        memory_id,
        request.content,
        request.metadata,
        request.reason or "手动更新 Profile 层记忆"
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Profile memory not found")
    
    return {
        "id": updated.id,
        "status": "success",
        "updated_at": updated.updated_at,
        "content": updated.content,
        "metadata": updated.meta_info,
        "layer": "profile"
    }

@router.put("/memory/user/{user_id}/event/{memory_id}")
async def update_user_event(user_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    updated = await user_memory.update_event(
        memory_id,
        request.content,
        request.metadata,
        request.reason or "手动更新 Event 层记忆"
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Event memory not found")
    
    return {
        "id": updated.id,
        "status": "success",
        "updated_at": updated.updated_at,
        "content": updated.content,
        "metadata": updated.meta_info,
        "layer": "event"
    }

@router.delete("/memory/user/{user_id}/profile/{memory_id}")
async def delete_user_profile(user_id: str, memory_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    success = await user_memory.delete_profile(memory_id, "手动删除 Profile 层记忆")
    if not success:
        raise HTTPException(status_code=404, detail="Profile memory not found")
    
    return {"id": memory_id, "status": "success", "layer": "profile", "message": "Profile memory deleted successfully"}

@router.delete("/memory/user/{user_id}/event/{memory_id}")
async def delete_user_event(user_id: str, memory_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")
    
    success = await user_memory.delete_event(memory_id, "手动删除 Event 层记忆")
    if not success:
        raise HTTPException(status_code=404, detail="Event memory not found")
    
    return {"id": memory_id, "status": "success", "layer": "event", "message": "Event memory deleted successfully"}

@router.put("/memory/agent/{agent_id}/profile/{memory_id}")
async def update_agent_profile(agent_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    updated = await agent_memory.update_profile(
        memory_id,
        request.content,
        request.metadata,
        request.reason or "手动更新 Agent Profile 层记忆"
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Agent Profile memory not found")
    
    return {
        "id": updated.id,
        "status": "success",
        "updated_at": updated.updated_at,
        "content": updated.content,
        "metadata": updated.meta_info,
        "layer": "profile"
    }

@router.put("/memory/agent/{agent_id}/event/{memory_id}")
async def update_agent_event(agent_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    updated = await agent_memory.update_event(
        memory_id,
        request.content,
        request.metadata,
        request.reason or "手动更新 Agent Event 层记忆"
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Agent Event memory not found")
    
    return {
        "id": updated.id,
        "status": "success",
        "updated_at": updated.updated_at,
        "content": updated.content,
        "metadata": updated.meta_info,
        "layer": "event"
    }

@router.delete("/memory/agent/{agent_id}/profile/{memory_id}")
async def delete_agent_profile(agent_id: str, memory_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    success = await agent_memory.delete_profile(memory_id, "手动删除 Agent Profile 层记忆")
    if not success:
        raise HTTPException(status_code=404, detail="Agent Profile memory not found")
    
    return {"id": memory_id, "status": "success", "layer": "profile", "message": "Agent Profile memory deleted successfully"}

@router.delete("/memory/agent/{agent_id}/event/{memory_id}")
async def delete_agent_event(agent_id: str, memory_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")
    
    success = await agent_memory.delete_event(memory_id, "手动删除 Agent Event 层记忆")
    if not success:
        raise HTTPException(status_code=404, detail="Agent Event memory not found")
    
    return {"id": memory_id, "status": "success", "layer": "event", "message": "Agent Event memory deleted successfully"}
