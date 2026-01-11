from typing import List, Optional, Dict, Any
from datetime import datetime
from app.repositories.interfaces import (
    IMemoryRepository,
    IVectorRepository,
    ILogRepository,
    IEmbeddingService
)
from app.domain.enums import MemoryType, MemoryLayer, MemoryAction
from app.domain.dto import ExtractionResultDTO, ExtractedMemoryResultDTO, MemoryDTO
from app.core.agent import MemoryExtractor
from app.core.rl_extractor import RLEnhancedExtractor
from app.core.memory import EmbeddingService
from app.config import settings


class MemoryService:
    """记忆服务：统一的记忆业务逻辑"""

    def __init__(
        self,
        memory_repo: IMemoryRepository,
        log_repo: ILogRepository,
        embedding_service: IEmbeddingService,
        extractor: Optional[MemoryExtractor] = None,
        rl_extractor: Optional[RLEnhancedExtractor] = None
    ):
        self.memory_repo = memory_repo
        self.log_repo = log_repo
        self.embedding_service = embedding_service
        self.extractor = extractor or MemoryExtractor()
        self.rl_extractor = rl_extractor

    async def store(
        self,
        memory_type: MemoryType,
        entity_id: str,
        content: str,
        memory_layer: MemoryLayer = MemoryLayer.EVENT,
        metadata: Optional[Dict[str, Any]] = None,
        is_permanent: bool = False,
        expiry_date: Optional[datetime] = None
    ) -> str:
        """存储记忆"""
        embedding = await self.embedding_service.generate(content)
        metadata = metadata or {}

        if memory_layer == MemoryLayer.PROFILE:
            memory_id = await self.memory_repo.store_profile(
                memory_type, entity_id, content, metadata, embedding
            )
            await self._log_and_record(
                memory_id, MemoryLayer.PROFILE, MemoryAction.INSERT,
                f"插入新的 {memory_layer.value} 层记忆", metadata
            )
        else:
            memory_id = await self.memory_repo.store_event(
                memory_type, entity_id, content, metadata, embedding,
                is_permanent, expiry_date
            )
            await self._log_and_record(
                memory_id, MemoryLayer.EVENT, MemoryAction.INSERT,
                f"插入新的 {memory_layer.value} 层记忆", metadata
            )

        return memory_id

    async def extract_and_store(
        self,
        memory_type: MemoryType,
        entity_id: str,
        content: str,
        enable_rl: bool = True
    ) -> ExtractionResultDTO:
        """抽取并存储记忆"""
        existing_memories = await self._get_existing_memories(
            memory_type, entity_id
        )

        if enable_rl and settings.ENABLE_RL_FLYWHEEL:
            extracted = await self.rl_extractor.extract_memories(
                content, entity_id, memory_type.value, existing_memories
            )
        else:
            extracted = await self.extractor.extract_memories(
                content, entity_id, existing_memories
            )

        result = ExtractionResultDTO(
            mode="auto_extract",
            total_extracted=len(extracted),
            profile_count=0,
            event_count=0
        )

        for mem in extracted:
            action = mem.get("action", "insert")
            layer = MemoryLayer(mem.get("memory_layer", "event"))

            if layer == MemoryLayer.PROFILE:
                result.profile_count += 1
            else:
                result.event_count += 1

            if action == "ignore":
                result.ignored += 1
                if "memory_id" in mem:
                    await self._log_and_record(
                        mem["memory_id"], layer, MemoryAction.IGNORE,
                        mem.get("reason", ""), {}
                    )
                result.memories.append(
                    ExtractedMemoryResultDTO(
                        id=mem.get("memory_id", ""),
                        action=MemoryAction.IGNORE,
                        layer=layer,
                        reason=mem.get("reason", "")
                    )
                )

            elif action == "update":
                result.updated += 1
                if "memory_id" in mem:
                    await self._update_memory(
                        mem["memory_id"], layer,
                        mem.get("content"), mem.get("metadata"),
                        mem.get("reason", "")
                    )
                result.memories.append(
                    ExtractedMemoryResultDTO(
                        id=mem.get("memory_id", ""),
                        action=MemoryAction.UPDATE,
                        layer=layer,
                        reason=mem.get("reason", "")
                    )
                )

            else:
                result.inserted += 1
                memory_id = await self.store(
                    memory_type, entity_id,
                    mem.get("content"), layer,
                    mem.get("metadata")
                )
                result.memories.append(
                    ExtractedMemoryResultDTO(
                        id=memory_id,
                        action=MemoryAction.INSERT,
                        layer=layer,
                        reason=mem.get("reason", ""),
                        created_at=datetime.utcnow()
                    )
                )

        return result

    async def get_by_id(self, memory_id: str) -> Optional[MemoryDTO]:
        """根据 ID 获取记忆"""
        return await self.memory_repo.get_by_id(memory_id)

    async def get_profile(
        self,
        memory_type: MemoryType,
        entity_id: str
    ) -> List[MemoryDTO]:
        """获取 Profile 层记忆"""
        memories = await self.memory_repo.get_profile(memory_type, entity_id)
        return [
            MemoryDTO(**mem, memory_type=memory_type, entity_id=entity_id)
            for mem in memories
        ]

    async def get_events(
        self,
        memory_type: MemoryType,
        entity_id: str,
        limit: int = 100
    ) -> List[MemoryDTO]:
        """获取 Event 层记忆"""
        memories = await self.memory_repo.get_events(
            memory_type, entity_id, limit
        )
        return [
            MemoryDTO(**mem, memory_type=memory_type, entity_id=entity_id)
            for mem in memories
        ]

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ) -> bool:
        """更新记忆"""
        memory = await self.get_by_id(memory_id)
        if not memory:
            return False

        embedding = None
        if content:
            embedding = await self.embedding_service.generate(content)

        if memory.memory_layer == MemoryLayer.PROFILE:
            success = await self.memory_repo.update_profile(
                memory_id, content, metadata, embedding
            )
        else:
            success = await self.memory_repo.update_event(
                memory_id, content, metadata, embedding
            )

        if success:
            await self._log_and_record(
                memory_id, memory.memory_layer, MemoryAction.UPDATE,
                reason or "手动更新记忆", {}
            )

        return success

    async def delete(
        self,
        memory_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """删除记忆"""
        memory = await self.get_by_id(memory_id)
        if not memory:
            return False

        success = await self.memory_repo.delete_memory(memory_id)

        if success:
            await self._log_and_record(
                memory_id, memory.memory_layer, MemoryAction.DELETE,
                reason or "手动删除记忆", {}
            )

        return success

    async def get_logs(
        self,
        memory_id: str,
        memory_layer: Optional[MemoryLayer] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取记忆的操作日志"""
        return await self.log_repo.get_logs(memory_id, memory_layer, limit)

    async def query(
        self,
        memory_type: MemoryType,
        entity_id: str,
        query_text: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """查询记忆"""
        query_embedding = await self.embedding_service.generate(query_text)

        vector_results = await self.memory_repo.search(
            query_embedding, memory_type, entity_id, top_k
        )

        return vector_results

    async def _get_existing_memories(
        self,
        memory_type: MemoryType,
        entity_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取现有记忆用于上下文"""
        profiles = await self.get_profile(memory_type, entity_id)
        events = await self.get_events(memory_type, entity_id, limit)

        memories = []
        for p in profiles:
            memories.append({
                "id": p.id,
                "content": p.content,
                "metadata": p.metadata,
                "memory_layer": "profile"
            })
        for e in events:
            memories.append({
                "id": e.id,
                "content": e.content,
                "metadata": e.metadata,
                "memory_layer": "event"
            })

        return memories

    async def _log_and_record(
        self,
        memory_id: str,
        memory_layer: MemoryLayer,
        action: MemoryAction,
        reason: str,
        metadata: Dict[str, Any]
    ):
        """记录操作日志"""
        await self.log_repo.log_action(
            memory_id, memory_layer, action, reason, metadata
        )

    async def _update_memory(
        self,
        memory_id: str,
        layer: MemoryLayer,
        content: Optional[str],
        metadata: Optional[Dict[str, Any]],
        reason: str
    ):
        """更新记忆的内部方法"""
        embedding = None
        if content:
            embedding = await self.embedding_service.generate(content)

        if layer == MemoryLayer.PROFILE:
            await self.memory_repo.update_profile(
                memory_id, content, metadata, embedding
            )
        else:
            await self.memory_repo.update_event(
                memory_id, content, metadata, embedding
            )

        await self._log_and_record(memory_id, layer, MemoryAction.UPDATE, reason, {})
