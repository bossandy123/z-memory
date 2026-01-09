# 记忆分层说明

## 概述

Z-Memory 支持记忆分层管理，将记忆分成两个独立的表：

1. **ProfileMemory 表（画像层）**：记录长期、稳定的信息
2. **EventMemory 表（事件层）**：记录动态事件和行为

## 数据库表结构

### ProfileMemory 表（画像层）

```sql
CREATE TABLE profile_memories (
    id VARCHAR PRIMARY KEY,
    memory_type VARCHAR NOT NULL,      -- 'user' or 'agent'
    entity_id VARCHAR NOT NULL,          -- user_id or agent_id
    content TEXT NOT NULL,             -- 记忆内容
    metadata JSON,                   -- 元数据
    embedding_id VARCHAR,              -- 向量ID
    created_at TIMESTAMP,              -- 创建时间
    updated_at TIMESTAMP               -- 更新时间
    INDEX idx_profile_type_entity (memory_type, entity_id),
    INDEX idx_profile_created_at (created_at)
);
```

### EventMemory 表（事件层）

```sql
CREATE TABLE event_memories (
    id VARCHAR PRIMARY KEY,
    memory_type VARCHAR NOT NULL,      -- 'user' or 'agent'
    entity_id VARCHAR NOT NULL,          -- user_id or agent_id
    content TEXT NOT NULL,             -- 记忆内容
    metadata JSON,                   -- 元数据
    embedding_id VARCHAR,              -- 向量ID
    is_permanent BOOLEAN DEFAULT FALSE,    -- 是否永久保存
    expiry_date TIMESTAMP,              -- 过期时间
    created_at TIMESTAMP,              -- 创建时间
    updated_at TIMESTAMP,              -- 更新时间
    INDEX idx_event_type_entity (memory_type, entity_id),
    INDEX idx_event_created_at (created_at),
    INDEX idx_event_expiry (expiry_date)
);
```

### MemoryLog 表（操作日志）

```sql
CREATE TABLE memory_logs (
    id VARCHAR PRIMARY KEY,
    memory_id VARCHAR NOT NULL,          -- 关联的记忆ID
    memory_layer VARCHAR NOT NULL,        -- 'profile' or 'event'
    action VARCHAR NOT NULL,            -- 'insert', 'update', 'ignore', 'delete'
    reason TEXT NOT NULL,             -- 自然语言原因
    metadata JSON,                   -- 附加信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_memory_id (memory_id),
    INDEX idx_log_layer (memory_layer),
    INDEX idx_log_action (action),
    INDEX idx_log_created_at (created_at)
);
```

## 记忆层次特点

### Profile 层（画像层）

| 特性 | 说明 |
|------|------|
| **存储内容** | 长期、稳定的信息 |
| **典型信息** | 性格、能力、职业、学历、偏好等 |
| **更新频率** | 低（很少改变） |
| **重要性** | 高（长期保存） |
| **查询特点** | 用于快速了解画像 |
| **永久性** | 默认永久保存 |

### Event 层（事件层）

| 特性 | 说明 |
|------|------|
| **存储内容** | 动态事件和行为 |
| **典型信息** | 对话记录、日常行为、具体事件等 |
| **更新频率** | 高（持续增长） |
| **重要性** | 中等（可设置过期时间） |
| **查询特点** | 用于回顾和分析 |
| **永久性** | 可设置过期 |

## API 使用

### 存储到 Profile 层

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户是一名软件工程师，毕业于北京大学",
    "memory_layer": "profile"
  }'
```

### 存储到 Event 层

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天下午参加了技术分享会，讨论了人工智能的应用",
    "memory_layer": "event",
    "is_permanent": false
  }'
```

### 自动抽取（智能分层）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天告诉我他是一名软件工程师，毕业于北京大学。他下午参加了技术分享会。",
    "auto_extract": true
  }'
```

### 查询分层记忆

```bash
# 获取画像层
curl "http://localhost:8000/memory/user/user123/profile"

# 获取事件层
curl "http://localhost:8000/memory/user/user123/events?limit=50"
```

### 更新记忆（分表更新）

```bash
# 更新 Profile 层
curl -X PUT "http://localhost:8000/memory/user/user123/profile/{memory_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户是一名高级软件工程师",
    "reason": "补充了具体的职级信息"
  }'

# 更新 Event 层
curl -X PUT "http://localhost:8000/memory/user/user123/event/{memory_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户下午参加了技术分享会",
    "reason": "补充了会议的具体主题"
  }'
```

### 删除记忆（分表删除）

```bash
# 删除 Profile 层
curl -X DELETE "http://localhost:8000/memory/user/user123/profile/{memory_id}"

# 删除 Event 层
curl -X DELETE "http://localhost:8000/memory/user/user123/event/{memory_id}"
```

### 查询操作日志

```bash
curl "http://localhost:8000/memory/user_user123_1234567890.123/logs?memory_layer=profile"
```

## 记忆分类

### Profile 层分类

| 类型 | 说明 | 示例 |
|------|------|------|
| `preference` | 偏好 | 喜欢阅读、喜欢运动 |
| `ability` | 能力 | 擅长编程、英语流利 |
| `career` | 职业 | 软件工程师、产品经理 |
| `education` | 教育 | 北京大学、计算机系 |
| `personality` | 性格 | 开朗外向、内向安静 |
| `value` | 价值观 | 重视创新、追求完美 |

### Event 层分类

| 类型 | 说明 | 示例 |
|------|------|------|
| `conversation` | 对话 | 讨论了项目计划 |
| `meeting` | 会议 | 参加了技术分享会 |
| `action` | 行为 | 提交了代码 |
| `decision` | 决策 | 决定使用新的技术栈 |
| `event` | 事件 | 参加了公司年会 |
| `other` | 其他 | 其他事件 |

## 优势

### 1. 清晰分离

- 画像和事件完全独立存储
- 查询更高效
- 管理更清晰

### 2. 优化查询

- Profile 层查询专注于画像相关
- Event 层查询专注于事件相关
- 减少不必要的扫描

### 3. 灵活管理

- Profile 层可以设置定期清理策略
- Event 层可以设置自动过期时间
- 不同层可以有不同的保留策略

### 4. 性能优化

- 分表可以显著提高查询性能
- 减少单表数据量
- 便于索引和分区

## 最佳实践

1. **存储规则**：
   - 静态或半静态信息存 Profile 层
   - 动态行为和事件存 Event 层

2. **查询策略**：
   - 查询用户画像时只查 Profile 表
   - 查询行为历史时只查 Event 表

3. **数据维护**：
   - Event 层可以定期清理过期数据
   - Profile 层需要长期保留

4. **索引优化**：
   - Profile 层关注 entity_id 和 updated_at
   - Event 层关注 entity_id 和 created_at
   - 日志表关注 memory_id 和 action

## 注意事项

1. **查询现有记忆**：自动抽取时会同时查询两个表
2. **内存消耗**：两个表都会占用内存，建议合理规划容量
3. **Qdrant 集合**：向量存储也根据层分别索引
4. **日志记录**：所有操作都会记录日志，注意日志表的增长
