from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.repositories.interfaces import (
    IMemoryRepository,
    IVectorRepository,
    ILogRepository
)
from app.database.models import ProfileMemory, EventMemory, MemoryLog, async_session
from app.database.vector_store import QdrantStore
from app.domain.enums import MemoryType, MemoryLayer, MemoryAction
from sqlalchemy import select
import uuid


class PostgresMemoryRepository(IMemoryRepository):
    """PostgreSQL 记忆仓储实现"""

    def __init__(self, vector_repo: IVectorRepository = None):
        self.vector_store = QdrantStore()
        self.vector_repo = vector_repo

    async def store_profile(
        self,
        memory_type: MemoryType,
        entity_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float]
    ) -> str:
        async with async_session() as session:
            memory_id = f"{memory_type.value}_profile_{entity_id}_{datetime.now().timestamp()}"

            layer_metadata = metadata.copy()
            layer_metadata["memory_layer"] = "profile"
            embedding_uuid = await self.vector_store.insert(
                memory_id, embedding, memory_type, entity_id, layer_metadata
            )

            memory = ProfileMemory(
                id=memory_id,
                memory_type=memory_type.value,
                entity_id=entity_id,
                content=content,
                meta_info=metadata,
                embedding_id=str(embedding_uuid)
            )
            session.add(memory)
            await session.commit()

            return memory_id

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
        async with async_session() as session:
            memory_id = f"{memory_type.value}_event_{entity_id}_{datetime.now().timestamp()}"

            layer_metadata = metadata.copy()
            layer_metadata["memory_layer"] = "event"
            embedding_uuid = await self.vector_store.insert(
                memory_id, embedding, memory_type, entity_id, layer_metadata
            )

            memory = EventMemory(
                id=memory_id,
                memory_type=memory_type.value,
                entity_id=entity_id,
                content=content,
                meta_info=metadata,
                embedding_id=str(embedding_uuid),
                is_permanent=is_permanent,
                expiry_date=expiry_date
            )
            session.add(memory)
            await session.commit()

            return memory_id

    async def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            if memory:
                return {
                    "id": memory.id,
                    "memory_type": memory.memory_type,
                    "entity_id": memory.entity_id,
                    "content": memory.content,
                    "metadata": memory.meta_info,
                    "memory_layer": "profile",
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                    "embedding_id": memory.embedding_id
                }

            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            if memory:
                return {
                    "id": memory.id,
                    "memory_type": memory.memory_type,
                    "entity_id": memory.entity_id,
                    "content": memory.content,
                    "metadata": memory.meta_info,
                    "memory_layer": "event",
                    "is_permanent": memory.is_permanent,
                    "expiry_date": memory.expiry_date,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                    "embedding_id": memory.embedding_id
                }

            return None

    async def get_profile(
        self,
        memory_type: MemoryType,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(
                    ProfileMemory.memory_type == memory_type.value,
                    ProfileMemory.entity_id == entity_id
                ).order_by(ProfileMemory.updated_at.desc())
            )
            memories = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "metadata": m.meta_info,
                    "updated_at": m.updated_at,
                    "embedding_id": m.embedding_id
                }
                for m in memories
            ]

    async def get_events(
        self,
        memory_type: MemoryType,
        entity_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(
                    EventMemory.memory_type == memory_type.value,
                    EventMemory.entity_id == entity_id
                ).order_by(EventMemory.created_at.desc()).limit(limit)
            )
            memories = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "metadata": m.meta_info,
                    "created_at": m.created_at,
                    "is_permanent": m.is_permanent,
                    "expiry_date": m.expiry_date,
                    "embedding_id": m.embedding_id
                }
                for m in memories
            ]

    async def update_profile(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()

            if not memory:
                return False

            if content is not None:
                memory.content = content
            if metadata is not None:
                memory.meta_info = metadata

            memory.updated_at = datetime.now()
            await session.commit()

            if embedding:
                await self.vector_store.update(
                    memory.embedding_id,
                    embedding=embedding,
                    metadata=metadata or {}
                )

            return True

    async def update_event(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()

            if not memory:
                return False

            if content is not None:
                memory.content = content
            if metadata is not None:
                memory.meta_info = metadata

            memory.updated_at = datetime.now()
            await session.commit()

            if embedding:
                await self.vector_store.update(
                    memory.embedding_id,
                    embedding=embedding,
                    metadata=metadata or {}
                )

            return True

    async def delete_memory(self, memory_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()

            if memory:
                await self.vector_store.delete(
                    memory.embedding_id,
                    MemoryType(memory.memory_type),
                    memory.entity_id
                )
                await session.delete(memory)
                await session.commit()
                return True

            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()

            if memory:
                await self.vector_store.delete(
                    memory.embedding_id,
                    MemoryType(memory.memory_type),
                    memory.entity_id
                )
                await session.delete(memory)
                await session.commit()
                return True

            return False


class QdrantVectorRepository(IVectorRepository):
    """Qdrant 向量仓储实现"""

    def __init__(self):
        self.vector_store = QdrantStore()

    async def insert(
        self,
        memory_id: str,
        embedding: List[float],
        memory_type: MemoryType,
        entity_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        return await self.vector_store.insert(
            memory_id, embedding, memory_type.value, entity_id, metadata
        )

    async def update(
        self,
        vector_id: str,
        embedding: Optional[List[float]] = None,
        memory_type: Optional[MemoryType] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        return await self.vector_store.update(
            vector_id, embedding,
            memory_type.value if memory_type else None,
            entity_id, metadata
        )

    async def delete(
        self,
        vector_id: str,
        memory_type: MemoryType,
        entity_id: str
    ) -> bool:
        return await self.vector_store.delete(vector_id, memory_type.value, entity_id)

    async def search(
        self,
        query_embedding: List[float],
        memory_type: MemoryType,
        entity_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        return await self.vector_store.search(
            query_embedding, memory_type.value, entity_id, top_k
        )


class PostgresLogRepository(ILogRepository):
    """PostgreSQL 日志仓储实现"""

    async def log_action(
        self,
        memory_id: str,
        memory_layer: MemoryLayer,
        action: MemoryAction,
        reason: str,
        metadata: Dict[str, Any]
    ) -> str:
        async with async_session() as session:
            log = MemoryLog(
                id=str(uuid.uuid4()),
                memory_id=memory_id,
                memory_layer=memory_layer.value,
                action=action.value,
                reason=reason,
                meta_info=metadata
            )
            session.add(log)
            await session.commit()
            return log.id

    async def get_logs(
        self,
        memory_id: str,
        memory_layer: Optional[MemoryLayer] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        async with async_session() as session:
            query_stmt = select(MemoryLog).where(MemoryLog.memory_id == memory_id)

            if memory_layer:
                query_stmt = query_stmt.where(MemoryLog.memory_layer == memory_layer.value)

            result = await session.execute(
                query_stmt.order_by(MemoryLog.created_at.desc()).limit(limit)
            )
            logs = result.scalars().all()
            return [
                {
                    "id": log.id,
                    "memory_id": log.memory_id,
                    "memory_layer": log.memory_layer,
                    "action": log.action,
                    "reason": log.reason,
                    "metadata": log.meta_info,
                    "reward": log.reward,
                    "outcome": log.outcome,
                    "evaluated_at": log.evaluated_at,
                    "created_at": log.created_at
                }
                for log in logs
            ]

    async def update_reward(
        self,
        log_id: str,
        reward: float,
        outcome: Dict[str, Any]
    ) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog).where(MemoryLog.id == log_id)
            )
            log = result.scalar_one_or_none()

            if not log:
                return False

            log.reward = reward
            log.outcome = outcome
            log.evaluated_at = datetime.utcnow()
            await session.commit()
            return True

    async def get_pending_rewards(
        self,
        days_threshold: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog).where(
                    MemoryLog.reward.is_(None),
                    MemoryLog.evaluated_at.is_(None),
                    MemoryLog.created_at < threshold_date
                ).limit(limit)
            )
            logs = result.scalars().all()
            return [
                {
                    "id": log.id,
                    "memory_id": log.memory_id,
                    "memory_layer": log.memory_layer,
                    "action": log.action,
                    "created_at": log.created_at
                }
                for log in logs
            ]
