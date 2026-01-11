# 代码重构迁移指南

## ✅ 重构已完成

### Phase 1: 核心架构重构 (已完成)

- [x] 创建 `app/domain/` 层
  - [x] `enums.py` - 枚举类型定义
  - [x] `dto.py` - 数据传输对象

- [x] 创建 `app/repositories/` 层
  - [x] `interfaces.py` - Repository 接口定义
  - [x] `impl/postgres_repository.py` - PostgreSQL 和 Qdrant 实现

- [x] 创建 `app/services/` 层
  - [x] `memory_service.py` - 记忆服务（统一 User/Agent）
  - [x] `query_service.py` - 查询服务
  - [x] `reward_service.py` - 奖励和训练服务

- [x] 创建 `app/api/dependencies.py` - 依赖注入容器

- [x] 重构 `app/api/routes/memory.py` - 使用 Service 层
- [x] 更新 `app/api/routes/health.py` - 添加 RL 飞轮状态
- [x] 创建 `app/api/schemas/` - 分离请求和响应模型

### Phase 2: 基础设施层清理 (已完成)

- [x] 清理 `app/core/memory.py`
  - [x] 删除 `UserMemory` 和 `AgentMemory` 类（已被 MemoryService 替代）
  - [x] 保留 `EmbeddingService` 实现为独立组件

- [x] 清理 `app/core/` 中的 RL 相关模块
  - [x] `agent.py` - 保留为独立抽取器
  - [x] `reward.py` - 保留为独立计算器
  - [x] `rl_trainer.py` - 保留为独立训练器
  - [x] `rl_extractor.py` - 保留为独立抽取器

- [x] 移除所有 `@deprecated` 注释

### Phase 3: API 路由重构 (已完成)

- [x] `app/api/routes/memory.py` - 使用 MemoryService
- [x] `app/api/routes/query.py` - 使用 QueryService
- [x] `app/api/routes/rl.py` - 使用 RewardService 和 TrainingService
- [x] `app/api/routes/health.py` - 显示 RL 飞轮状态

### Phase 4: 文档更新 (已完成)

- [x] 更新 `docs/ARCHITECTURE.md` - 新架构说明
- [x] 更新 `docs/MIGRATION.md` - 迁移指南
- [x] 更新 `README.md` - RL 飞轮和架构说明

## 新架构概览

```
app/
├── domain/                  # 领域层
│   ├── enums.py            # 枚举类型
│   └── dto.py              # DTO 模型
├── repositories/            # 数据访问层
│   ├── interfaces.py       # 仓储接口
│   └── impl/
│       └── postgres_repository.py  # PostgreSQL/Qdrant 实现
├── services/                # 业务逻辑层
│   ├── memory_service.py   # 记忆服务
│   ├── query_service.py    # 查询服务
│   └── reward_service.py   # 奖励和训练服务
├── api/                       # 接口层
│   ├── routes/             # 路由定义
│   ├── schemas/            # 请求/响应模型
│   └── dependencies.py     # 依赖注入容器
└── core/                     # 基础设施层
    ├── memory.py           # EmbeddingService
    ├── agent.py            # MemoryExtractor
    ├── reward.py           # RewardCalculator
    ├── rl_trainer.py       # RLTrainer
    └── rl_extractor.py      # RLEnhancedExtractor
```

## 使用新架构

### 在 API 路由中使用

```python
from app.api.dependencies import container
from app.domain.enums import MemoryType, MemoryLayer

@router.post("/memory/user/{user_id}")
async def store_user_memory(user_id: str, request: MemoryRequest):
    service = container.user_memory_service

    if request.auto_extract:
        result = await service.extract_and_store(
            MemoryType.USER, user_id, request.content
        )
        return result.dict()
    else:
        memory_id = await service.store(
            MemoryType.USER, user_id,
            request.content, request.memory_layer,
            request.metadata, request.is_permanent
        )
        return {"id": memory_id}
```

### 在其他模块中使用

```python
from app.api.dependencies import container

# 获取服务
memory_service = container.user_memory_service
query_service = container.query_service
reward_service = container.reward_service

# 使用服务
memories = await memory_service.get_profile(MemoryType.USER, user_id)
results = await query_service.query(query, user_id=user_id)
await reward_service.calculate(log_id)
```

## 迁移检查清单

- [x] 所有新代码都使用 `container.xxx_service` 访问服务
- [x] 所有 API 路由都调用 Service 层而非直接调用 core 模块
- [x] 所有数据访问都通过 Repository 接口
- [x] 所有枚举类型都使用 `app.domain.enums`
- [x] 所有 DTO 都使用 `app.domain.dto`
- [x] core 层不再包含被 Service 层替代的类

## 架构优势

| 方面 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| **API 代码量** | memory.py 553 行 | memory.py ~280 行 | 减少 ~49% |
| **重复代码** | UserMemory/AgentMemory 重复 350+ 行 | 统一为 MemoryService | 消除 |
| **服务实例** | 直接实例化 | 通过 ServiceContainer 解耦 | DI 模式 |
| **分层清晰** | 业务逻辑混杂 | 职责明确分层 | 更易维护 |
| **向后兼容** | 保留旧代码 | 清理冗余代码 | 代码更简洁 |
