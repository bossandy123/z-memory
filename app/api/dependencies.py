from typing import Optional, Any
from app.repositories.interfaces import (
    IMemoryRepository,
    IVectorRepository,
    ILogRepository
)
from app.repositories.impl.postgres_repository import (
    PostgresMemoryRepository,
    QdrantVectorRepository,
    PostgresLogRepository
)
from app.services.memory_service import MemoryService
from app.services.query_service import QueryService
from app.services.reward_service import RewardService, TrainingService
from app.core.agent import MemoryExtractor
from app.core.rl_extractor import RLEnhancedExtractor
from app.core.memory import EmbeddingService
from app.config import settings


class ServiceContainer:
    """依赖注入容器"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        self._memory_repo: Any = None
        self._vector_repo: Any = None
        self._log_repo: Any = None
        self._embedding_service: Any = None
        self._memory_extractor: Any = None
        self._rl_extractor: Any = None
        self._user_memory_service: Any = None
        self._agent_memory_service: Any = None
        self._query_service: Any = None
        self._reward_service: Any = None
        self._training_service: Any = None

    @property
    def memory_repo(self):
        if self._memory_repo is None:
            self._memory_repo = PostgresMemoryRepository()
        return self._memory_repo

    @property
    def vector_repo(self):
        if self._vector_repo is None:
            self._vector_repo = QdrantVectorRepository()
        return self._vector_repo

    @property
    def log_repo(self):
        if self._log_repo is None:
            self._log_repo = PostgresLogRepository()
        return self._log_repo

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    @property
    def memory_extractor(self):
        if self._memory_extractor is None:
            self._memory_extractor = MemoryExtractor()
        return self._memory_extractor

    @property
    def rl_extractor(self):
        if self._rl_extractor is None:
            self._rl_extractor = RLEnhancedExtractor(
                enable_rl=settings.ENABLE_RL_FLYWHEEL
            )
        return self._rl_extractor

    @property
    def user_memory_service(self):
        if self._user_memory_service is None and settings.ENABLE_USER_MEMORY:
            self._user_memory_service = MemoryService(
                memory_repo=self.memory_repo,
                log_repo=self.log_repo,
                embedding_service=self.embedding_service,
                extractor=self.memory_extractor,
                rl_extractor=self.rl_extractor
            )
        return self._user_memory_service

    @property
    def agent_memory_service(self):
        if self._agent_memory_service is None and settings.ENABLE_AGENT_MEMORY:
            self._agent_memory_service = MemoryService(
                memory_repo=self.memory_repo,
                log_repo=self.log_repo,
                embedding_service=self.embedding_service,
                extractor=self.memory_extractor,
                rl_extractor=self.rl_extractor
            )
        return self._agent_memory_service

    @property
    def query_service(self):
        if self._query_service is None:
            self._query_service = QueryService(
                user_memory_service=self.user_memory_service,
                agent_memory_service=self.agent_memory_service
            )
        return self._query_service

    @property
    def reward_service(self):
        if self._reward_service is None:
            self._reward_service = RewardService(log_repo=self.log_repo)
        return self._reward_service

    @property
    def training_service(self):
        if self._training_service is None:
            self._training_service = TrainingService()
        return self._training_service


container = ServiceContainer()
