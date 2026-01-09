from app.database.models import ProfileMemory, EventMemory, MemoryLog, async_session, init_db
from app.database.vector_store import QdrantStore
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from openai import AsyncOpenAI
from app.config import settings
from sqlalchemy import select
import dashscope
from dashscope import TextEmbedding
import uuid

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class EmbeddingService:
    @staticmethod
    async def generate(text: str) -> List[float]:
        if settings.EMBEDDING_PROVIDER == "dashscope":
            return await EmbeddingService._generate_dashscope(text)
        else:
            return await EmbeddingService._generate_openai(text)
    
    @staticmethod
    async def _generate_dashscope(text: str) -> List[float]:
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        response = TextEmbedding.call(
            model=settings.DASHSCOPE_EMBEDDING_MODEL,
            input=text
        )
        if response.status_code == 200:
            return response.output['embeddings'][0]['embedding']
        else:
            raise Exception(f"DashScope API error: {response.message}")
    
    @staticmethod
    async def _generate_openai(text: str) -> List[float]:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

class MemoryLogger:
    @staticmethod
    async def log_action(
        memory_id: str, 
        memory_layer: str,
        action: str, 
        reason: str, 
        metadata: Dict[str, Any] = None
    ):
        async with async_session() as session:
            log = MemoryLog(
                id=str(uuid.uuid4()),
                memory_id=memory_id,
                memory_layer=memory_layer,
                action=action,
                reason=reason,
                metadata=metadata or {}
            )
            session.add(log)
            await session.commit()

class UserMemory:
    def __init__(self):
        self.vector_store = QdrantStore()

    async def store_profile(self, user_id: str, content: str, 
                         metadata: Dict[str, Any] = None) -> ProfileMemory:
        async with async_session() as session:
            memory_id = f"user_profile_{user_id}_{datetime.now().timestamp()}"
            embedding = await EmbeddingService.generate(content)
            
            # Store in Qdrant first to get UUID
            layer_metadata = metadata or {}
            layer_metadata["memory_layer"] = "profile"
            embedding_uuid = await self.vector_store.insert(memory_id, embedding, "user", user_id, layer_metadata)
            
            # Store in PostgreSQL
            memory = ProfileMemory(
                id=memory_id,
                memory_type="user",
                entity_id=user_id,
                content=content,
                metadata=metadata or {},
                embedding_id=str(embedding_uuid)
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "profile",
                "insert",
                f"插入新的 profile 层记忆",
                {"auto_extracted": False}
            )
            
            return memory
    
    async def store_event(self, user_id: str, content: str, 
                       metadata: Dict[str, Any] = None,
                       is_permanent: bool = False,
                       expiry_date: Optional[datetime] = None) -> EventMemory:
        async with async_session() as session:
            memory_id = f"user_event_{user_id}_{datetime.now().timestamp()}"
            embedding = await EmbeddingService.generate(content)
            
            # Store in Qdrant first to get UUID
            layer_metadata = metadata or {}
            layer_metadata["memory_layer"] = "event"
            embedding_uuid = await self.vector_store.insert(memory_id, embedding, "user", user_id, layer_metadata)
            
            # Store in PostgreSQL
            memory = EventMemory(
                id=memory_id,
                memory_type="user",
                entity_id=user_id,
                content=content,
                metadata=metadata or {},
                embedding_id=str(embedding_uuid),
                is_permanent=is_permanent,
                expiry_date=expiry_date
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "event",
                "insert",
                f"插入新的 event 层记忆",
                {"is_permanent": is_permanent, "auto_extracted": False}
            )
            
            return memory

    async def update_profile(self, user_id: str, memory_id: str, 
                         content: Optional[str] = None, 
                         metadata: Optional[Dict[str, Any]] = None,
                         reason: Optional[str] = None) -> Optional[ProfileMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            update_reason = reason or "手动更新"
            
            # Update content if provided
            if content is not None:
                memory.content = content
                new_embedding = await EmbeddingService.generate(content)
                layer_metadata = metadata or memory.meta_info
                layer_metadata["memory_layer"] = "profile"
                await self.vector_store.update(memory.embedding_id, new_embedding, "user", 
                                             user_id, layer_metadata)
            else:
                update_reason = reason or "更新元数据"
            
            # Update metadata if provided
            if metadata is not None:
                memory.meta_info = metadata
                if content is None:
                    layer_metadata = metadata
                    layer_metadata["memory_layer"] = "profile"
                    await self.vector_store.update(memory.embedding_id, None, "user", 
                                                 user_id, layer_metadata)
            
            memory.updated_at = datetime.now()
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "profile",
                "update",
                update_reason,
                {"updated_fields": list(metadata.keys()) if metadata else ["content"]}
            )
            
            return memory

    async def update_event(self, user_id: str, memory_id: str, 
                       content: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None,
                       reason: Optional[str] = None) -> Optional[EventMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            update_reason = reason or "手动更新"
            
            # Update content if provided
            if content is not None:
                memory.content = content
                new_embedding = await EmbeddingService.generate(content)
                layer_metadata = metadata or memory.meta_info
                layer_metadata["memory_layer"] = "event"
                await self.vector_store.update(memory.embedding_id, new_embedding, "user", 
                                             user_id, layer_metadata)
            else:
                update_reason = reason or "更新元数据"
            
            # Update metadata if provided
            if metadata is not None:
                memory.meta_info = metadata
                if content is None:
                    layer_metadata = metadata
                    layer_metadata["memory_layer"] = "event"
                    await self.vector_store.update(memory.embedding_id, None, "user", 
                                                 user_id, layer_metadata)
            
            memory.updated_at = datetime.now()
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "event",
                "update",
                update_reason,
                {"updated_fields": list(metadata.keys()) if metadata else ["content"]}
            )
            
            return memory

    async def delete_profile(self, user_id: str, memory_id: str, reason: Optional[str] = None) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from Qdrant using embedding_id (UUID)
            await self.vector_store.delete(memory.embedding_id, "user", user_id)
            
            # Delete from PostgreSQL
            await session.delete(memory)
            await session.commit()
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "profile",
                "delete",
                reason or "手动删除",
                {}
            )
            
            return True

    async def delete_event(self, user_id: str, memory_id: str, reason: Optional[str] = None) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from Qdrant using embedding_id (UUID)
            await self.vector_store.delete(memory.embedding_id, "user", user_id)
            
            # Delete from PostgreSQL
            await session.delete(memory)
            await session.commit()
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "event",
                "delete",
                reason or "手动删除",
                {}
            )
            
            return True

    async def query(self, user_id: str, query: str, top_k: int = 5, 
                   memory_layer: Optional[str] = None) -> List[Union[ProfileMemory, EventMemory]]:
        query_embedding = await EmbeddingService.generate(query)
        
        # Search in Qdrant
        vector_results = await self.vector_store.search(query_embedding, "user", user_id, top_k)
        
        # Get full memories from PostgreSQL
        memory_ids = [r["memory_id"] for r in vector_results]
        results = []
        
        for memory_id in memory_ids:
            # Try Profile table first
            async with async_session() as session:
                result = await session.execute(
                    select(ProfileMemory).where(ProfileMemory.id == memory_id)
                )
                profile = result.scalar_one_or_none()
                if profile:
                    if not memory_layer or memory_layer == "profile":
                        results.append(profile)
                        continue
            
            # Try Event table
            async with async_session() as session:
                result = await session.execute(
                    select(EventMemory).where(EventMemory.id == memory_id)
                )
                event = result.scalar_one_or_none()
                if event:
                    if not memory_layer or memory_layer == "event":
                        results.append(event)
        
        return results

    async def get_by_id(self, memory_id: str) -> Optional[Union[ProfileMemory, EventMemory]]:
        # Try Profile table first
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            if memory:
                return memory
        
        # Try Event table
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            return result.scalar_one_or_none()

    async def get_profile(self, user_id: str) -> List[ProfileMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory)
                .where(
                    ProfileMemory.memory_type == "user",
                    ProfileMemory.entity_id == user_id
                )
                .order_by(ProfileMemory.updated_at.desc())
            )
            return result.scalars().all()

    async def get_events(self, user_id: str, limit: int = 100) -> List[EventMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory)
                .where(
                    EventMemory.memory_type == "user",
                    EventMemory.entity_id == user_id
                )
                .order_by(EventMemory.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_logs(self, memory_id: str, memory_layer: Optional[str] = None, 
                   limit: int = 10) -> List[MemoryLog]:
        async with async_session() as session:
            query_stmt = select(MemoryLog).where(MemoryLog.memory_id == memory_id)
            
            if memory_layer:
                query_stmt = query_stmt.where(MemoryLog.memory_layer == memory_layer)
            
            result = await session.execute(
                query_stmt.order_by(MemoryLog.created_at.desc()).limit(limit)
            )
            return result.scalars().all()

class AgentMemory:
    def __init__(self):
        self.vector_store = QdrantStore()

    async def store_profile(self, agent_id: str, content: str, 
                         metadata: Dict[str, Any] = None) -> ProfileMemory:
        async with async_session() as session:
            memory_id = f"agent_profile_{agent_id}_{datetime.now().timestamp()}"
            embedding = await EmbeddingService.generate(content)
            
            # Store in Qdrant first to get UUID
            layer_metadata = metadata or {}
            layer_metadata["memory_layer"] = "profile"
            embedding_uuid = await self.vector_store.insert(memory_id, embedding, "agent", agent_id, layer_metadata)
            
            # Store in PostgreSQL
            memory = ProfileMemory(
                id=memory_id,
                memory_type="agent",
                entity_id=agent_id,
                content=content,
                metadata=metadata or {},
                embedding_id=str(embedding_uuid)
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "profile",
                "insert",
                f"插入新的 profile 层记忆",
                {"auto_extracted": False}
            )
            
            return memory
    
    async def store_event(self, agent_id: str, content: str, 
                       metadata: Dict[str, Any] = None,
                       is_permanent: bool = False,
                       expiry_date: Optional[datetime] = None) -> EventMemory:
        async with async_session() as session:
            memory_id = f"agent_event_{agent_id}_{datetime.now().timestamp()}"
            embedding = await EmbeddingService.generate(content)
            
            # Store in PostgreSQL
            memory = EventMemory(
                id=memory_id,
                memory_type="agent",
                entity_id=agent_id,
                content=content,
                metadata=metadata or {},
                embedding_id=memory_id,
                is_permanent=is_permanent,
                expiry_date=expiry_date
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Store in Qdrant first to get UUID
            layer_metadata = metadata or {}
            layer_metadata["memory_layer"] = "event"
            embedding_uuid = await self.vector_store.insert(memory_id, embedding, "agent", agent_id, layer_metadata)
            
            # Store in PostgreSQL
            memory = EventMemory(
                id=memory_id,
                memory_type="agent",
                entity_id=agent_id,
                content=content,
                metadata=metadata or {},
                embedding_id=str(embedding_uuid),
                is_permanent=is_permanent,
                expiry_date=expiry_date
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "event",
                "insert",
                f"插入新的 event 层记忆",
                {"is_permanent": is_permanent, "auto_extracted": False}
            )
            
            return memory

    async def update_profile(self, agent_id: str, memory_id: str, 
                         content: Optional[str] = None, 
                         metadata: Optional[Dict[str, Any]] = None,
                         reason: Optional[str] = None) -> Optional[ProfileMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            update_reason = reason or "手动更新"
            
            # Update content if provided
            if content is not None:
                memory.content = content
                new_embedding = await EmbeddingService.generate(content)
                layer_metadata = metadata or memory.meta_info
                layer_metadata["memory_layer"] = "profile"
                await self.vector_store.update(memory.embedding_id, new_embedding, "agent", 
                                             agent_id, layer_metadata)
            else:
                update_reason = reason or "更新元数据"
            
            # Update metadata if provided
            if metadata is not None:
                memory.meta_info = metadata
                if content is None:
                    layer_metadata = metadata
                    layer_metadata["memory_layer"] = "profile"
                    await self.vector_store.update(memory.embedding_id, None, "agent", 
                                                 agent_id, layer_metadata)
            
            memory.updated_at = datetime.now()
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "profile",
                "update",
                update_reason,
                {"updated_fields": list(metadata.keys()) if metadata else ["content"]}
            )
            
            return memory

    async def update_event(self, agent_id: str, memory_id: str, 
                       content: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None,
                       reason: Optional[str] = None) -> Optional[EventMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            update_reason = reason or "手动更新"
            
            # Update content if provided
            if content is not None:
                memory.content = content
                new_embedding = await EmbeddingService.generate(content)
                layer_metadata = metadata or memory.meta_info
                layer_metadata["memory_layer"] = "event"
                await self.vector_store.update(memory.embedding_id, new_embedding, "agent", 
                                             agent_id, layer_metadata)
            else:
                update_reason = reason or "更新元数据"
            
            # Update metadata if provided
            if metadata is not None:
                memory.meta_info = metadata
                if content is None:
                    layer_metadata = metadata
                    layer_metadata["memory_layer"] = "event"
                    await self.vector_store.update(memory.embedding_id, None, "agent", 
                                                 agent_id, layer_metadata)
            
            memory.updated_at = datetime.now()
            await session.commit()
            await session.refresh(memory)
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "event",
                "update",
                update_reason,
                {"updated_fields": list(metadata.keys()) if metadata else ["content"]}
            )
            
            return memory

    async def delete_profile(self, agent_id: str, memory_id: str, reason: Optional[str] = None) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from Qdrant using embedding_id (UUID)
            await self.vector_store.delete(memory.embedding_id, "agent", agent_id)
            
            # Delete from PostgreSQL
            await session.delete(memory)
            await session.commit()
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "profile",
                "delete",
                reason or "手动删除",
                {}
            )
            
            return True

    async def delete_event(self, agent_id: str, memory_id: str, reason: Optional[str] = None) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from Qdrant using embedding_id (UUID)
            await self.vector_store.delete(memory.embedding_id, "agent", agent_id)
            
            # Delete from PostgreSQL
            await session.delete(memory)
            await session.commit()
            
            # Record log
            await MemoryLogger.log_action(
                memory_id,
                "event",
                "delete",
                reason or "手动删除",
                {}
            )
            
            return True

    async def query(self, agent_id: str, query: str, top_k: int = 5, 
                   memory_layer: Optional[str] = None) -> List[Union[ProfileMemory, EventMemory]]:
        query_embedding = await EmbeddingService.generate(query)
        
        # Search in Qdrant
        vector_results = await self.vector_store.search(query_embedding, "agent", agent_id, top_k)
        
        # Get full memories from PostgreSQL
        memory_ids = [r["memory_id"] for r in vector_results]
        results = []
        
        for memory_id in memory_ids:
            # Try Profile table first
            async with async_session() as session:
                result = await session.execute(
                    select(ProfileMemory).where(ProfileMemory.id == memory_id)
                )
                profile = result.scalar_one_or_none()
                if profile:
                    if not memory_layer or memory_layer == "profile":
                        results.append(profile)
                        continue
            
            # Try Event table
            async with async_session() as session:
                result = await session.execute(
                    select(EventMemory).where(EventMemory.id == memory_id)
                )
                event = result.scalar_one_or_none()
                if event:
                    if not memory_layer or memory_layer == "event":
                        results.append(event)
        
        return results

    async def get_profile(self, agent_id: str) -> List[ProfileMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(ProfileMemory)
                .where(
                    ProfileMemory.memory_type == "agent",
                    ProfileMemory.entity_id == agent_id
                )
                .order_by(ProfileMemory.updated_at.desc())
            )
            return result.scalars().all()

    async def get_events(self, agent_id: str, limit: int = 100) -> List[EventMemory]:
        async with async_session() as session:
            result = await session.execute(
                select(EventMemory)
                .where(
                    EventMemory.memory_type == "agent",
                    EventMemory.entity_id == agent_id
                )
                .order_by(EventMemory.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
    
    async def get_logs(self, memory_id: str, memory_layer: Optional[str] = None, 
                   limit: int = 10) -> List[MemoryLog]:
        async with async_session() as session:
            query_stmt = select(MemoryLog).where(MemoryLog.memory_id == memory_id)
            
            if memory_layer:
                query_stmt = query_stmt.where(MemoryLog.memory_layer == memory_layer)
            
            result = await session.execute(
                query_stmt.order_by(MemoryLog.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
