from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class MemoryRequest(BaseModel):
    """记忆存储请求"""
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auto_extract: bool = False
    memory_layer: Optional[str] = None
    is_permanent: bool = False


class UpdateMemoryRequest(BaseModel):
    """记忆更新请求"""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class ExtractionRequest(BaseModel):
    """记忆抽取请求"""
    content: str
    enable_rl: bool = False


class RewardCalculateRequest(BaseModel):
    """奖励计算请求"""
    log_id: str
    days_since_creation: int = 7


class RewardEvaluateRequest(BaseModel):
    """批量奖励评估请求"""
    limit: int = 100
    days_threshold: int = 7


class TrainModelRequest(BaseModel):
    """训练模型请求"""
    days: int = 30
    epochs: int = 10
    save_checkpoint: bool = True


class FeedbackRequest(BaseModel):
    """反馈请求"""
    memory_id: str
    actual_outcome: Dict[str, Any]


class QueryMemoryRequest(BaseModel):
    """查询记忆请求"""
    query: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    top_k: int = 5
