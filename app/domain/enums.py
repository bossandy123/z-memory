from enum import Enum


class MemoryType(str, Enum):
    """记忆类型枚举"""
    USER = "user"
    AGENT = "agent"


class MemoryLayer(str, Enum):
    """记忆层级枚举"""
    PROFILE = "profile"
    EVENT = "event"


class MemoryAction(str, Enum):
    """记忆操作枚举"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    IGNORE = "ignore"
    QUERY = "query"


class MemoryCategory(str, Enum):
    """记忆分类枚举"""
    PREFERENCE = "preference"
    ABILITY = "ability"
    CAREER = "career"
    EDUCATION = "education"
    PERSONALITY = "personality"
    EVENT = "event"
    OTHER = "other"


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"


class EmbeddingProvider(str, Enum):
    """Embedding 提供商枚举"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"
