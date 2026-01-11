from fastapi import APIRouter, HTTPException
from typing import Optional
from app.api.schemas.memory import MemoryRequest, UpdateMemoryRequest
from app.api.dependencies import container
from app.domain.enums import MemoryType, MemoryLayer
from app.config import settings

router = APIRouter()


def _get_memory_layer(layer: Optional[str]) -> MemoryLayer:
    if layer:
        return MemoryLayer(layer)
    return MemoryLayer.EVENT


@router.post("/memory/user/{user_id}")
async def store_user_memory(user_id: str, request: MemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    memory_layer = _get_memory_layer(request.memory_layer)

    if request.auto_extract:
        result = await service.extract_and_store(
            MemoryType.USER, user_id, request.content
        )
        return result.dict()
    else:
        memory_id = await service.store(
            MemoryType.USER, user_id,
            request.content, memory_layer,
            request.metadata, request.is_permanent
        )
        return {
            "id": memory_id,
            "status": "success",
            "mode": "direct",
            "layer": memory_layer.value
        }


@router.post("/memory/agent/{agent_id}")
async def store_agent_memory(agent_id: str, request: MemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    memory_layer = _get_memory_layer(request.memory_layer)

    if request.auto_extract:
        result = await service.extract_and_store(
            MemoryType.AGENT, agent_id, request.content
        )
        return result.dict()
    else:
        memory_id = await service.store(
            MemoryType.AGENT, agent_id,
            request.content, memory_layer,
            request.metadata, request.is_permanent
        )
        return {
            "id": memory_id,
            "status": "success",
            "mode": "direct",
            "layer": memory_layer.value
        }


@router.get("/memory/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    memories = await service.get_profile(MemoryType.USER, user_id)

    return {
        "user_id": user_id,
        "layer": "profile",
        "count": len(memories),
        "memories": [m.dict() for m in memories]
    }


@router.get("/memory/user/{user_id}/events")
async def get_user_events(user_id: str, limit: int = 100):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    memories = await service.get_events(MemoryType.USER, user_id, limit)

    return {
        "user_id": user_id,
        "layer": "event",
        "count": len(memories),
        "memories": [m.dict() for m in memories]
    }


@router.get("/memory/agent/{agent_id}/profile")
async def get_agent_profile(agent_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="Agent memory service not available")

    memories = await service.get_profile(MemoryType.AGENT, agent_id)

    return {
        "agent_id": agent_id,
        "layer": "profile",
        "count": len(memories),
        "memories": [m.dict() for m in memories]
    }


@router.get("/memory/agent/{agent_id}/events")
async def get_agent_events(agent_id: str, limit: int = 100):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="Agent memory service not available")

    memories = await service.get_events(MemoryType.AGENT, agent_id, limit)

    return {
        "agent_id": agent_id,
        "layer": "event",
        "count": len(memories),
        "memories": [m.dict() for m in memories]
    }


@router.get("/memory/{memory_id}/logs")
async def get_memory_logs(memory_id: str, memory_layer: str, limit: int = 10):
    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    logs = await service.get_logs(memory_id, MemoryLayer(memory_layer), limit)

    return {
        "memory_id": memory_id,
        "memory_layer": memory_layer,
        "count": len(logs),
        "logs": logs
    }


@router.put("/memory/user/{user_id}/profile/{memory_id}")
async def update_user_profile(user_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    success = await service.update(
        memory_id, request.content, request.metadata,
        request.reason or "手动更新 Profile 层记忆"
    )

    if not success:
        raise HTTPException(status_code=404, detail="Profile memory not found")

    memory = await service.get_by_id(memory_id)
    return {
        "id": memory_id,
        "status": "success",
        "content": memory.content if memory else None,
        "metadata": memory.metadata if memory else None,
        "layer": "profile"
    }


@router.put("/memory/user/{user_id}/event/{memory_id}")
async def update_user_event(user_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    success = await service.update(
        memory_id, request.content, request.metadata,
        request.reason or "手动更新 Event 层记忆"
    )

    if not success:
        raise HTTPException(status_code=404, detail="Event memory not found")

    memory = await service.get_by_id(memory_id)
    return {
        "id": memory_id,
        "status": "success",
        "content": memory.content if memory else None,
        "metadata": memory.metadata if memory else None,
        "layer": "event"
    }


@router.delete("/memory/user/{user_id}/profile/{memory_id}")
async def delete_user_profile(user_id: str, memory_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    success = await service.delete(memory_id, "手动删除 Profile 层记忆")

    if not success:
        raise HTTPException(status_code=404, detail="Profile memory not found")

    return {"id": memory_id, "status": "success", "layer": "profile", "message": "Profile memory deleted successfully"}


@router.delete("/memory/user/{user_id}/event/{memory_id}")
async def delete_user_event(user_id: str, memory_id: str):
    if not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=503, detail="User memory is not enabled")

    service = container.user_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="User memory service not available")

    success = await service.delete(memory_id, "手动删除 Event 层记忆")

    if not success:
        raise HTTPException(status_code=404, detail="Event memory not found")

    return {"id": memory_id, "status": "success", "layer": "event", "message": "Event memory deleted successfully"}


@router.put("/memory/agent/{agent_id}/profile/{memory_id}")
async def update_agent_profile(agent_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="Agent memory service not available")

    success = await service.update(
        memory_id, request.content, request.metadata,
        request.reason or "手动更新 Agent Profile 层记忆"
    )

    if not success:
        raise HTTPException(status_code=404, detail="Agent Profile memory not found")

    memory = await service.get_by_id(memory_id)
    return {
        "id": memory_id,
        "status": "success",
        "content": memory.content if memory else None,
        "metadata": memory.metadata if memory else None,
        "layer": "profile"
    }


@router.put("/memory/agent/{agent_id}/event/{memory_id}")
async def update_agent_event(agent_id: str, memory_id: str, request: UpdateMemoryRequest):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="Agent memory service not available")

    success = await service.update(
        memory_id, request.content, request.metadata,
        request.reason or "手动更新 Agent Event 层记忆"
    )

    if not success:
        raise HTTPException(status_code=404, detail="Agent Event memory not found")

    memory = await service.get_by_id(memory_id)
    return {
        "id": memory_id,
        "status": "success",
        "content": memory.content if memory else None,
        "metadata": memory.metadata if memory else None,
        "layer": "event"
    }


@router.delete("/memory/agent/{agent_id}/profile/{memory_id}")
async def delete_agent_profile(agent_id: str, memory_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="Agent memory service not available")

    success = await service.delete(memory_id, "手动删除 Agent Profile 层记忆")

    if not success:
        raise HTTPException(status_code=404, detail="Agent Profile memory not found")

    return {"id": memory_id, "status": "success", "layer": "profile", "message": "Agent Profile memory deleted successfully"}


@router.delete("/memory/agent/{agent_id}/event/{memory_id}")
async def delete_agent_event(agent_id: str, memory_id: str):
    if not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=503, detail="Agent memory is not enabled")

    service = container.agent_memory_service
    if not service:
        raise HTTPException(status_code=503, detail="Agent memory service not available")

    success = await service.delete(memory_id, "手动删除 Agent Event 层记忆")

    if not success:
        raise HTTPException(status_code=404, detail="Agent Event memory not found")

    return {"id": memory_id, "status": "success", "layer": "event", "message": "Agent Event memory deleted successfully"}
