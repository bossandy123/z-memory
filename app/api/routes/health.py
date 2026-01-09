from fastapi import APIRouter
from datetime import datetime
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "features": {
            "user_memory_enabled": settings.ENABLE_USER_MEMORY,
            "agent_memory_enabled": settings.ENABLE_AGENT_MEMORY
        }
    }

@router.get("/config")
async def get_config():
    return {
        "user_memory_enabled": settings.ENABLE_USER_MEMORY,
        "agent_memory_enabled": settings.ENABLE_AGENT_MEMORY,
        "embedding_provider": settings.EMBEDDING_PROVIDER
    }
