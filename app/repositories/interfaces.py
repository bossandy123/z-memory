from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.enums import MemoryType, MemoryLayer, MemoryAction


class IMemoryRepository(ABC):
    """记忆仓储接口"""

    @abstractmethod
    async def store_profile(
        self,
        memory_type: MemoryType,
        entity_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float]
    ) -> str:
        """存储 Profile 层记忆，返回记忆 ID"""
        pass

    @abstractmethod
    async def store_event(
        self,
        memory_type: MemoryType,
        entity_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float],
        is_permanent: bool = False,
        expiry_date: Optional[datetime] = None
    ) -> str:
        """存储 Event 层记忆，返回记忆 ID"""
        pass

    @abstractmethod
    async def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取记忆"""
        pass

    @abstractmethod
    async def get_profile(
        self,
        memory_type: MemoryType,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        """获取 Profile 层记忆列表"""
        pass

    @abstractmethod
    async def get_events(
        self,
        memory_type: MemoryType,
        entity_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取 Event 层记忆列表"""
        pass

    @abstractmethod
    async def update_profile(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """更新 Profile 层记忆"""
        pass

    @abstractmethod
    async def update_event(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """更新 Event 层记忆"""
        pass

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        pass


class IVectorRepository(ABC):
    """向量仓储接口"""

    @abstractmethod
    async def insert(
        self,
        memory_id: str,
        embedding: List[float],
        memory_type: MemoryType,
        entity_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """插入向量，返回向量 ID"""
        pass

    @abstractmethod
    async def update(
        self,
        vector_id: str,
        embedding: Optional[List[float]] = None,
        memory_type: Optional[MemoryType] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        pass

    @abstractmethod
    async def delete(
        self,
        vector_id: str,
        memory_type: MemoryType,
        entity_id: str
    ) -> bool:
        """删除向量"""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        memory_type: MemoryType,
        entity_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索向量"""
        pass


class ILogRepository(ABC):
    """日志仓储接口"""

    @abstractmethod
    async def log_action(
        self,
        memory_id: str,
        memory_layer: MemoryLayer,
        action: MemoryAction,
        reason: str,
        metadata: Dict[str, Any]
    ) -> str:
        """记录操作日志，返回日志 ID"""
        pass

    @abstractmethod
    async def get_logs(
        self,
        memory_id: str,
        memory_layer: Optional[MemoryLayer] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取记忆的操作日志"""
        pass

    @abstractmethod
    async def update_reward(
        self,
        log_id: str,
        reward: float,
        outcome: Dict[str, Any]
    ) -> bool:
        """更新日志奖励"""
        pass

    @abstractmethod
    async def get_pending_rewards(
        self,
        days_threshold: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取待评估奖励的日志"""
        pass


class IEmbeddingService(ABC):
    """Embedding 服务接口"""

    @abstractmethod
    async def generate(self, text: str) -> List[float]:
        """生成文本向量"""
        pass
