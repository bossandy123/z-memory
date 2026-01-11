# 架构设计

## 分层架构

Z-Memory 采用经典的 DDD（领域驱动设计）分层架构：

```
┌─────────────────────────────────────────────────────────┐
│                       API Layer                           │
│              (Thin Controllers, Schemas)              │
├─────────────────────────────────────────────────────────┤
│                    Service Layer                        │
│           (Business Logic Coordination)                │
├─────────────────────────────────────────────────────────┤
│                  Repository Layer                      │
│              (Data Access Abstraction)               │
├─────────────────────────────────────────────────────────┤
│               Infrastructure Layer                     │
│      (Database, Vector Store, LLM, Embeddings)       │
├─────────────────────────────────────────────────────────┤
│                   Domain Layer                         │
│          (Enums, DTOs, Business Models)             │
└─────────────────────────────────────────────────────────┘
```

## 层级职责

| 层级 | 职责 | 模块 |
|------|------|------|
| **API** | HTTP 接口、请求/响应转换 | `app/api/` |
| **Service** | 业务逻辑协调 | `app/services/` |
| **Repository** | 数据访问抽象 | `app/repositories/` |
| **Infrastructure** | 技术实现 | `app/database/`, `app/core/` |
| **Domain** | 领域模型 | `app/domain/` |

## 目录结构

```
app/
├── api/                    # API 层
│   ├── routes/            # 路由（Thin Controller）
│   │   ├── health.py
│   │   ├── memory.py        # 使用 Service 层
│   │   ├── query.py
│   │   └── rl.py
│   └── dependencies.py     # 依赖注入容器
│
├── domain/                 # 领域层
│   ├── enums.py            # 枚举类型
│   └── dto.py              # 数据传输对象
│
├── repositories/            # Repository 层
│   ├── interfaces.py       # 仓储接口定义
│   └── impl/
│       └── postgres_repository.py  # PostgreSQL/Qdrant 实现
│
├── services/                # Service 层
│   ├── memory_service.py   # 记忆服务
│   ├── query_service.py    # 查询服务
│   └── reward_service.py   # 奖励和训练服务
│
├── core/                   # 基础设施层
│   ├── memory.py           # EmbeddingService（待迁移）
│   ├── agent.py            # MemoryExtractor（待迁移）
│   ├── reward.py           # RewardCalculator（待迁移）
│   ├── rl_trainer.py       # RLTrainer（待迁移）
│   └── rl_extractor.py    # RLEnhancedExtractor（待迁移）
│
└── database/               # 基础设施层
    ├── models.py           # SQLAlchemy 模型
    └── vector_store.py     # Qdrant 客户端
```

## 新旧架构对比

### API 层代码量

| 文件 | 旧代码行数 | 新代码行数 | 减少比例 |
|------|----------|----------|----------|
| `memory.py` | 553 | ~280 | 49% |
| `query.py` | 45 | ~60 | -33% |

### 核心改进

| 改进点 | 重构前 | 重构后 |
|--------|--------|--------|
| **重复代码** | UserMemory/AgentMemory 共 350+ 行 | 统一为 MemoryService |
| **依赖关系** | API 直接依赖多个 core 模块 | 通过 ServiceContainer 解耦 |
| **测试性** | 直接调用数据库 | 通过接口可 Mock |
| **扩展性** | 新功能需要修改多处 | 在对应层添加即可 |
| **可维护性** | 职责混杂 | 职责清晰分层 |

## 依赖注入

使用 `ServiceContainer` 管理所有服务实例：

```python
from app.api.dependencies import container

service = container.user_memory_service
result = await service.extract_and_store(
    MemoryType.USER, user_id, content
)
```

## 待迁移模块

以下模块仍在 `app/core/` 中，计划逐步迁移到新架构：

- `memory.py` - EmbeddingService 迁移到 infrastructure/llm/
- `agent.py` - MemoryExtractor 迁移到 infrastructure/llm/
- `reward.py` - RewardCalculator 迁移到 services/
- `rl_trainer.py` - RLTrainer 迁移到 services/
- `rl_extractor.py` - RLEnhancedExtractor 迁移到 services/

## 迁移路径

### 第一阶段（已完成）
- ✅ Domain 层创建
- ✅ Repository 接口和实现
- ✅ Service 层核心服务
- ✅ API 路由重构
- ✅ 依赖注入容器

### 第二阶段（待完成）
- �️ LLM 和 Embedding 迁移到 infrastructure/llm/
- �️ RewardCalculator 迁移到 services/
- �️ RLTrainer 和 RLEnhancedExtractor 迁移到 services/
- ⏅ 测试用例更新

### 第三阶段（待完成）
- �️ 删除旧代码
- �️ 更新所有文档
- �️ 性能优化和监控
