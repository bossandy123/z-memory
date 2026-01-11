from sqlalchemy import Column, String, DateTime, JSON, Text, Index, Boolean, ForeignKey, Float
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
    memory_layer = Column(String, nullable=False)
    action = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    meta_info = Column("metadata", JSON, default={})
    reward = Column(Float, nullable=True)
    outcome = Column("outcome", JSON, default={})
    evaluated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_log_memory_id', 'memory_id'),
        Index('idx_log_layer', 'memory_layer'),
        Index('idx_log_action', 'action'),
        Index('idx_log_created_at', 'created_at'),
        Index('idx_log_reward', 'reward'),
        Index('idx_log_evaluated', 'evaluated_at'),
    )

class RLTrainingSample(Base):
    """强化学习训练样本表：存储RL训练的数据"""
    __tablename__ = "rl_training_samples"

    id = Column(String, primary_key=True)
    log_id = Column(String, ForeignKey('memory_logs.id'), nullable=False)
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)

    state = Column(JSON, nullable=False)
    action = Column(String, nullable=False)
    reward = Column(Float, nullable=False)
    next_state = Column(JSON, nullable=True)
    done = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_rl_log_id', 'log_id'),
        Index('idx_rl_entity', 'entity_type', 'entity_id'),
        Index('idx_rl_reward', 'reward'),
        Index('idx_rl_created_at', 'created_at'),
    )

class RLModelCheckpoint(Base):
    """强化学习模型检查点表：存储训练好的模型"""
    __tablename__ = "rl_model_checkpoints"

    id = Column(String, primary_key=True)
    model_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    model_data = Column(JSON, nullable=False)
    metrics = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_rl_model_name', 'model_name'),
        Index('idx_rl_model_version', 'version'),
    )

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
