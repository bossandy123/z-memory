from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/zmemory"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_PREFIX: str = "zmemory"
    
    # 功能开关
    ENABLE_USER_MEMORY: bool = True
    ENABLE_AGENT_MEMORY: bool = True
    
    # LLM 配置（用于自动抽取记忆）
    LLM_PROVIDER: str = "dashscope"
    LLM_MODEL: str = "qwen-plus"
    LLM_TEMPERATURE: float = 0.7
    
    # OpenAI 配置（可选）
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIM: int = 1536
    OPENAI_LLM_MODEL: str = "gpt-4"
    
    # 阿里云 DashScope 配置（推荐）
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v2"
    DASHSCOPE_EMBEDDING_DIM: int = 1024
    DASHSCOPE_LLM_MODEL: str = "qwen-plus"
    
    # Embedding 提供商: "openai" 或 "dashscope"
    EMBEDDING_PROVIDER: str = "dashscope"

    # RL 飞轮配置
    ENABLE_RL_FLYWHEEL: bool = True
    RL_MODEL_NAME: str = "memory_policy"
    RL_TEMPERATURE: float = 0.5

    # 奖励计算配置
    REWARD_HIT_WEIGHT: float = 1.0
    REWARD_QUALITY_WEIGHT: float = 0.5
    REWARD_TIME_DECAY_FACTOR: float = 0.95

    # 训练配置
    RL_TRAINING_DAYS: int = 30
    RL_TRAINING_EPOCHS: int = 10
    RL_TRAINING_LEARNING_RATE: float = 0.01

    # 评估配置
    REWARD_EVALUATION_DAYS_THRESHOLD: int = 7
    REWARD_EVALUATION_BATCH_SIZE: int = 100

    def validate_config(self):
        if not self.ENABLE_USER_MEMORY and not self.ENABLE_AGENT_MEMORY:
            raise ValueError("至少需要启用 USER_MEMORY 或 AGENT_MEMORY 中的一个")

    class Config:
        env_file = ".env"

settings = Settings()
settings.validate_config()
