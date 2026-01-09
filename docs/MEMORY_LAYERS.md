# 记忆分层文档

## 概述

Z-Memory 支持记忆分层管理：

### 1. Profile 层（画像表）
记录长期、稳定的信息：性格、能力、职业、学历、偏好等

### 2. Event 层（事件表）
记录动态事件和行为：对话记录、日常行为、具体事件等

## 数据库表结构

三个独立表：

- `profile_memories` - 画像表
- `event_memories` - 事件表
- `memory_logs` - 操作日志表

## 使用方式

### 分层存储

```bash
# 存储 Profile 层
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户是一名软件工程师，毕业于北京大学",
    "memory_layer": "profile"
  }'

# 存储 Event 层
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天下午参加了技术分享会",
    "memory_layer": "event",
    "is_permanent": false
  }'
```

### 分层查询

```bash
# 查询画像
curl "http://localhost:8000/memory/user/user123/profile"

# 查询事件
curl "http://localhost:8000/memory/user/user123/events?limit=50"
```

### 分层更新

```bash
# 更新 Profile 层
curl -X PUT "http://localhost:8000/memory/user/user123/profile/{memory_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户是一名高级软件工程师",
    "reason": "补充了职级信息"
  }'

# 更新 Event 层
curl -X PUT "http://localhost:8000/memory/user/user123/event/{memory_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户下午参加了技术分享会",
    "reason": "补充了会议主题"
  }'
```

### 分层删除

```bash
# 删除 Profile 层
curl -X DELETE "http://localhost:8000/memory/user/user123/profile/{memory_id}"

# 删除 Event 层
curl -X DELETE "http://localhost:8000/memory/user/user123/event/{memory_id}"
```

详细说明请参考 [记忆分层文档](docs/SEPARATE_LAYERS.md)
