from sqlalchemy import Column, String, DateTime, JSON, Text, Index, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.config import settings

Base = declarative_base()

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class ProfileMemory(Base):
    """Profile 层记忆表：记录长期、稳定的信息"""
    __tablename__ = "profile_memories"
    
    id = Column(String, primary_key=True)
    memory_type = Column(String, nullable=False)  # 'user' or 'agent'
    entity_id = Column(String, nullable=False)  # user_id or agent_id
    content = Column(Text, nullable=False)
    meta_info = Column("metadata", JSON, default={})
    embedding_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_profile_type_entity', 'memory_type', 'entity_id'),
        Index('idx_profile_created_at', 'created_at'),
    )

class EventMemory(Base):
    """Event 层记忆表：记录动态事件和行为"""
    __tablename__ = "event_memories"
    
    id = Column(String, primary_key=True)
    memory_type = Column(String, nullable=False)  # 'user' or 'agent'
    entity_id = Column(String, nullable=False)  # user_id or agent_id
    content = Column(Text, nullable=False)
    meta_info = Column("metadata", JSON, default={})
    embedding_id = Column(String, nullable=True)
    is_permanent = Column(Boolean, default=False)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_event_type_entity', 'memory_type', 'entity_id'),
        Index('idx_event_created_at', 'created_at'),
        Index('idx_event_expiry', 'expiry_date'),
    )

class MemoryLog(Base):
    """记忆操作日志表：记录所有记忆操作的原因"""
    __tablename__ = "memory_logs"
    
    id = Column(String, primary_key=True)
    memory_id = Column(String, nullable=False)
    memory_layer = Column(String, nullable=False)  # 'profile' or 'event'
    action = Column(String, nullable=False)  # 'update', 'ignore', 'insert', 'delete'
    reason = Column(Text, nullable=False)  # 自然语言原因
    meta_info = Column("metadata", JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_log_memory_id', 'memory_id'),
        Index('idx_log_layer', 'memory_layer'),
        Index('idx_log_action', 'action'),
        Index('idx_log_created_at', 'created_at'),
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
