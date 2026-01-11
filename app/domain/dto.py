from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.domain.enums import MemoryType, MemoryLayer, MemoryAction, MemoryCategory


class MemoryDTO(BaseModel):
    """记忆数据传输对象"""
    id: str
    memory_type: MemoryType
    entity_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    memory_layer: Optional[MemoryLayer] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileMemoryDTO(MemoryDTO):
    """Profile 层记忆 DTO"""
    memory_layer: MemoryLayer = MemoryLayer.PROFILE


class EventMemoryDTO(MemoryDTO):
    """Event 层记忆 DTO"""
    memory_layer: MemoryLayer = MemoryLayer.EVENT
    is_permanent: bool = False
    expiry_date: Optional[datetime] = None


class MemoryLogDTO(BaseModel):
    """记忆日志 DTO"""
    id: str
    memory_id: str
    memory_layer: MemoryLayer
    action: MemoryAction
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reward: Optional[float] = None
    outcome: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryActionDTO(BaseModel):
    """记忆操作请求 DTO"""
    action: MemoryAction
    reason: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionDTO(BaseModel):
    """记忆抽取 DTO"""
    content: str
    action: MemoryAction
    reason: str
    existing_content: Optional[str] = None
    memory_layer: MemoryLayer = MemoryLayer.EVENT
    memory_type: MemoryCategory = MemoryCategory.OTHER
    importance: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)
    memory_id: Optional[str] = None


class ExtractedMemoryResultDTO(BaseModel):
    """抽取记忆结果 DTO"""
    id: str
    action: MemoryAction
    layer: MemoryLayer
    reason: str
    status: str = "success"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExtractionResultDTO(BaseModel):
    """抽取结果汇总 DTO"""
    mode: str
    total_extracted: int
    inserted: int = 0
    updated: int = 0
    ignored: int = 0
    profile_count: int = 0
    event_count: int = 0
    memories: list[ExtractedMemoryResultDTO] = Field(default_factory=list)
