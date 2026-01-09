from app.database.models import Memory, async_session, init_db
from app.database.vector_store import QdrantStore
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from app.config import settings
from sqlalchemy import select
import dashscope
from dashscope import TextEmbedding

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

class UserMemory:
    def __init__(self):
        self.vector_store = QdrantStore()

    async def store(self, user_id: str, content: str, 
                   metadata: Dict[str, Any] = None) -> Memory:
        async with async_session() as session:
            memory_id = f"user_{user_id}_{datetime.now().timestamp()}"
            embedding = await EmbeddingService.generate(content)
            
            # Store in PostgreSQL
            memory = Memory(
                id=memory_id,
                memory_type="user",
                entity_id=user_id,
                content=content,
                metadata=metadata or {},
                embedding_id=memory_id
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Store in Qdrant
            await self.vector_store.insert(memory_id, embedding, "user", user_id, metadata)
            
            return memory

    async def update(self, memory_id: str, content: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[Memory]:
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            # Update content if provided
            if content is not None:
                memory.content = content
                new_embedding = await EmbeddingService.generate(content)
                await self.vector_store.update(memory_id, new_embedding, memory.memory_type, 
                                             memory.entity_id, metadata or memory.meta_info)
            
            # Update metadata if provided
            if metadata is not None:
                memory.meta_info = metadata
                if content is None:
                    await self.vector_store.update(memory_id, None, memory.memory_type, 
                                                 memory.entity_id, metadata)
            
            memory.updated_at = datetime.now()
            await session.commit()
            await session.refresh(memory)
            
            return memory

    async def delete(self, memory_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from Qdrant
            await self.vector_store.delete(memory_id, memory.memory_type, memory.entity_id)
            
            # Delete from PostgreSQL
            await session.delete(memory)
            await session.commit()
            
            return True

    async def query(self, user_id: str, query: str, top_k: int = 5) -> List[Memory]:
        query_embedding = await EmbeddingService.generate(query)
        
        # Search in Qdrant
        vector_results = await self.vector_store.search(query_embedding, "user", user_id, top_k)
        
        # Get full memories from PostgreSQL
        memory_ids = [r["memory_id"] for r in vector_results]
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id.in_(memory_ids))
            )
            return result.scalars().all()

    async def get_by_id(self, memory_id: str) -> Optional[Memory]:
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            return result.scalar_one_or_none()

class AgentMemory:
    def __init__(self):
        self.vector_store = QdrantStore()

    async def store(self, agent_id: str, content: str, 
                   metadata: Dict[str, Any] = None) -> Memory:
        async with async_session() as session:
            memory_id = f"agent_{agent_id}_{datetime.now().timestamp()}"
            embedding = await EmbeddingService.generate(content)
            
            # Store in PostgreSQL
            memory = Memory(
                id=memory_id,
                memory_type="agent",
                entity_id=agent_id,
                content=content,
                metadata=metadata or {},
                embedding_id=memory_id
            )
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Store in Qdrant
            await self.vector_store.insert(memory_id, embedding, "agent", agent_id, metadata)
            
            return memory

    async def update(self, memory_id: str, content: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[Memory]:
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return None
            
            # Update content if provided
            if content is not None:
                memory.content = content
                new_embedding = await EmbeddingService.generate(content)
                await self.vector_store.update(memory_id, new_embedding, memory.memory_type, 
                                             memory.entity_id, metadata or memory.meta_info)
            
            # Update metadata if provided
            if metadata is not None:
                memory.meta_info = metadata
                if content is None:
                    await self.vector_store.update(memory_id, None, memory.memory_type, 
                                                 memory.entity_id, metadata)
            
            memory.updated_at = datetime.now()
            await session.commit()
            await session.refresh(memory)
            
            return memory

    async def delete(self, memory_id: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id == memory_id)
            )
            memory = result.scalar_one_or_none()
            
            if not memory:
                return False
            
            # Delete from Qdrant
            await self.vector_store.delete(memory_id, memory.memory_type, memory.entity_id)
            
            # Delete from PostgreSQL
            await session.delete(memory)
            await session.commit()
            
            return True

    async def query(self, agent_id: str, query: str, top_k: int = 5) -> List[Memory]:
        query_embedding = await EmbeddingService.generate(query)
        
        # Search in Qdrant
        vector_results = await self.vector_store.search(query_embedding, "agent", agent_id, top_k)
        
        # Get full memories from PostgreSQL
        memory_ids = [r["memory_id"] for r in vector_results]
        async with async_session() as session:
            result = await session.execute(
                select(Memory).where(Memory.id.in_(memory_ids))
            )
            return result.scalars().all()
