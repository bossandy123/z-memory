from sqlalchemy import Column, String, DateTime, JSON, Text, Index
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.config import settings

Base = declarative_base()

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(String, primary_key=True)
    memory_type = Column(String, nullable=False)  # 'user' or 'agent'
    entity_id = Column(String, nullable=False)  # user_id or agent_id
    content = Column(Text, nullable=False)
    meta_info = Column("metadata", JSON, default={})
    embedding_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_memory_type_entity', 'memory_type', 'entity_id'),
        Index('idx_created_at', 'created_at'),
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
