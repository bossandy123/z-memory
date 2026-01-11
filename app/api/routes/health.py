from fastapi import APIRouter, Depends
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.api.dependencies import container
from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    features: dict


class ConfigResponse(BaseModel):
    user_memory_enabled: bool
    agent_memory_enabled: bool
    embedding_provider: str
    rl_flywheel_enabled: bool
    model_version: Optional[str] = None


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "features": {
            "user_memory_enabled": settings.ENABLE_USER_MEMORY,
            "agent_memory_enabled": settings.ENABLE_AGENT_MEMORY
        }
    }


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    training_service=Depends(lambda: container.training_service)
):
    model_version = None
    if training_service and training_service.trainer.model_weights:
        model_version = training_service.trainer.model_weights.get("version")

    return {
        "user_memory_enabled": settings.ENABLE_USER_MEMORY,
        "agent_memory_enabled": settings.ENABLE_AGENT_MEMORY,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "rl_flywheel_enabled": settings.ENABLE_RL_FLYWHEEL,
        "model_version": model_version
    }
