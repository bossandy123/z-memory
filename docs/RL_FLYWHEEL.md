# RL 飞轮学习机制

## 概述

RL（Reinforcement Learning）飞轮学习机制是 Z-Memory 的智能优化系统，它通过从 Why-Log（操作日志）中学习，不断优化记忆抽取策略，实现自我改进的闭环。

## 核心概念

### 1. RL 与 Why-Log 的对应关系

| RL 要素 | Why-Log 中的对应 |
|---------|-----------------|
| **状态 (State)** | 现有记忆 + 新输入内容 + 历史操作日志 |
| **动作 (Action)** | insert / update / ignore / delete |
| **奖励 (Reward)** | 从记忆使用情况、质量变化推导 |
| **策略 (Policy)** | LLM 的记忆抽取决策逻辑 |

### 2. 飞轮循环

```
┌─────────────────────────────────────────────────────────────┐
│                    RL 飞轮学习循环                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 操作执行                                                  │
│     └─> 执行记忆操作（insert/update/ignore/delete）        │
│         记录到 Why-Log                                      │
│                                                             │
│  2. 数据收集                                                  │
│     └─> Why-Log (决策+原因)                                 │
│     └─> 记忆使用频率统计                                    │
│     └─> 记忆质量评分                                        │
│                                                             │
│  3. 奖励评估                                                  │
│     └─> RewardCalculator 计算奖励                           │
│     └─> insert → 后续查询命中 → 正奖励                     │
│     └─> ignore → 后续发现有价值 → 负奖励                   │
│     └─> update → 记忆质量提升 → 正奖励                     │
│                                                             │
│  4. 训练优化                                                  │
│     └─> RLTrainer 从 Why-Log 训练                          │
│     └─> 生成训练样本 (state, action, reward, next_state)  │
│     └─> 更新策略模型                                        │
│                                                             │
│  5. 策略应用                                                  │
│     └─> RLEnhancedExtractor 使用训练后的策略              │
│     └─> 辅助/增强 LLM 决策                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 架构设计

### 核心模块

```
app/core/
├── reward.py          # RewardCalculator - 奖励计算器
├── rl_trainer.py      # RLTrainer - 强化学习训练器
└── rl_extractor.py     # RLEnhancedExtractor - RL增强抽取器
```

### 数据模型扩展

```
memory_logs 表扩展：
  - reward (FLOAT): 奖励值
  - outcome (JSONB): 效果评估结果
  - evaluated_at (TIMESTAMP): 奖励评估时间

新增表：
  - rl_training_samples: 训练样本存储
  - rl_model_checkpoints: 模型检查点存储
```

## 使用指南

### 1. 启用 RL 飞轮

在 `.env` 文件中设置：

```env
# 启用 RL 飞轮
ENABLE_RL_FLYWHEEL=true

# RL 模型配置
RL_MODEL_NAME=memory_policy
RL_TEMPERATURE=0.5

# 奖励计算配置
REWARD_HIT_WEIGHT=1.0
REWARD_QUALITY_WEIGHT=0.5
REWARD_TIME_DECAY_FACTOR=0.95
```

### 2. 数据库迁移

```bash
# 执行迁移
python scripts/migrate_rl.py migrate

# 检查迁移状态
python scripts/migrate_rl.py status

# 回滚（慎用）
python scripts/migrate_rl.py rollback
```

### 3. 手动评估奖励

```bash
# 评估单个日志的奖励
curl -X POST "http://localhost:8000/rl/reward/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "log_id": "log_abc123",
    "days_since_creation": 7
  }'
```

### 4. 批量评估奖励

```bash
# 批量评估未计算的奖励
curl -X POST "http://localhost:8000/rl/reward/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 100,
    "days_threshold": 7
  }'
```

### 5. 训练模型

```bash
# 训练 RL 模型
curl -X POST "http://localhost:8000/rl/train" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 30,
    "epochs": 10,
    "save_checkpoint": true
  }'
```

### 6. 运行完整流程

```bash
# 运行完整的 RL 飞轮流程
curl -X GET "http://localhost:8000/rl/pipeline/run?days=7&train=true"
```

## API 端点

### 奖励计算

| 端点 | 方法 | 说明 |
|------|------|------|
| `/rl/reward/calculate` | POST | 计算单个日志的奖励 |
| `/rl/reward/evaluate` | POST | 批量评估奖励 |
| `/rl/reward/statistics` | GET | 获取奖励统计信息 |

### 模型训练

| 端点 | 方法 | 说明 |
|------|------|------|
| `/rl/train` | POST | 训练 RL 模型 |
| `/rl/training/samples` | GET | 获取训练样本 |
| `/rl/model/statistics` | GET | 获取模型统计信息 |
| `/rl/model/save` | POST | 保存模型检查点 |
| `/rl/model/load` | POST | 加载最新模型 |

### 抽取器

| 端点 | 方法 | 说明 |
|------|------|------|
| `/rl/extractor/feedback` | POST | 提交反馈用于训练 |
| `/rl/extractor/statistics` | GET | 获取抽取器统计信息 |

### 系统

| 端点 | 方法 | 说明 |
|------|------|------|
| `/rl/pipeline/run` | GET | 运行完整流程 |
| `/rl/health` | GET | 健康检查 |

## 奖励机制

### INSERT 奖励

```
reward = (查询命中次数 × hit_weight) × 时间衰减
```

- 查询命中次数：该记忆在时间窗口内被查询的次数
- 时间衰减：基于创建时间的指数衰减

### UPDATE 奖励

```
reward = (查询命中奖励 × hit_weight + 质量提升 × quality_weight) × 时间衰减
```

- 查询命中奖励：同 INSERT
- 质量提升：基于 memory.metadata.quality_score

### IGNORE 奖励

```
reward = 相似记忆数量 × 0.5
```

- 相似记忆数量：与被忽略记忆相似的现有记忆数量

### DELETE 奖励

```
if (最近查询次数 < 0.1):
    reward = 0.5
else:
    reward = -0.3
```

## 配置参数

### 奖励计算参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `REWARD_HIT_WEIGHT` | 1.0 | 查询命中权重 |
| `REWARD_QUALITY_WEIGHT` | 0.5 | 质量提升权重 |
| `REWARD_TIME_DECAY_FACTOR` | 0.95 | 时间衰减因子 |

### 训练参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RL_TRAINING_DAYS` | 30 | 收集最近 N 天的数据 |
| `RL_TRAINING_EPOCHS` | 10 | 训练轮数 |
| `RL_TRAINING_LEARNING_RATE` | 0.01 | 学习率 |

### 评估参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `REWARD_EVALUATION_DAYS_THRESHOLD` | 7 | 只评估 N 天前的日志 |
| `REWARD_EVALUATION_BATCH_SIZE` | 100 | 批量评估大小 |

## 最佳实践

### 1. 初始阶段

```bash
# 1. 禁用 RL，先使用纯 LLM 抽取
ENABLE_RL_FLYWHEEL=false

# 2. 运行一段时间，收集 Why-Log 数据（建议 1-2 周）

# 3. 启用 RL
ENABLE_RL_FLYWHEEL=true

# 4. 首次训练
python scripts/migrate_rl.py migrate
curl -X POST "http://localhost:8000/rl/reward/evaluate" \
  -d '{"limit": 1000, "days_threshold": 7}'
curl -X POST "http://localhost:8000/rl/train" \
  -d '{"days": 30, "epochs": 10}'
```

### 2. 持续优化

```bash
# 每周运行一次完整流程
0 2 * * 1 curl -X GET "http://localhost:8000/rl/pipeline/run?days=7&train=true"
```

### 3. 监控指标

```bash
# 定期查看统计信息
curl "http://localhost:8000/rl/reward/statistics?days=30"
curl "http://localhost:8000/rl/model/statistics"
```

## 性能优化

### 1. 批量评估

```python
# 一次性评估多个日志，减少数据库查询
result = await calculator.batch_evaluate_rewards(
    limit=1000,
    days_threshold=7
)
```

### 2. 异步训练

```python
# 在后台异步训练，不阻塞主流程
import asyncio
asyncio.create_task(trainer.run_training_pipeline(
    days=30,
    epochs=10,
    save_checkpoint=True
))
```

### 3. 模型缓存

```python
# 加载模型后缓存，避免重复加载
await trainer.load_latest_model()
# 使用 trainer.model_weights
```

## 注意事项

1. **数据质量**：RL 的效果取决于 Why-Log 的质量
2. **冷启动**：初始阶段需要足够的训练数据
3. **奖励设计**：合理的奖励函数是关键
4. **模型更新**：定期更新模型以适应新的数据分布
5. **A/B 测试**：新模型上线前进行 A/B 测试

## 故障排查

### 问题：训练样本不足

```bash
# 检查样本数量
curl "http://localhost:8000/rl/training/samples?days=30"

# 解决方案：增加数据收集时间或降低 days 阈值
```

### 问题：奖励均为 0

```bash
# 检查奖励评估配置
curl "http://localhost:8000/rl/reward/statistics"

# 检查是否有查询日志
# 解决方案：确保有足够的查询活动
```

### 问题：模型不收敛

```bash
# 降低学习率
RL_TRAINING_LEARNING_RATE=0.001

# 增加训练轮数
RL_TRAINING_EPOCHS=20
```

## 相关文档

- [Why-Log 说明](./WHY_LOG.md)
- [智能抽取详细说明](./SMART_EXTRACT.md)
- [API 文档](./API.md)
