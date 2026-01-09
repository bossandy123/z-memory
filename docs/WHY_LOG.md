# Why-Log 功能说明

## 概述

在 Auto 模式下自动更新或废弃记忆时，系统会自动记录 Why-Log（操作原因日志），用自然语言说明为什么要更新或忽略某条记忆。

## Why-Log 的作用

1. **透明性**：了解记忆变化的原因
2. **可追溯**：完整的记忆操作历史
3. **调试**：理解 LLM 的决策逻辑
4. **优化**：根据日志优化记忆抽取策略

## Why-Log 记录场景

### 1. INSERT（插入新记忆）

```json
{
  "action": "insert",
  "reason": "插入新的event层记忆"
}
```

### 2. UPDATE（更新现有记忆）

```json
{
  "action": "update",
  "reason": "新的信息更详细，包含了用户的职业背景和工作经验"
}
```

### 3. IGNORE（忽略重复记忆）

```json
{
  "action": "ignore",
  "reason": "这条记忆与现有记忆完全相同，无需重复存储"
}
```

## API 使用

### 自动抽取（自动记录 Why-Log）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天告诉我他是一名软件工程师，毕业于北京大学。他昨天也说过同样的事情。",
    "auto_extract": true
  }'
```

**响应示例**：
```json
{
  "mode": "auto_extract",
  "total_extracted": 1,
  "inserted": 0,
  "updated": 0,
  "ignored": 1,
  "profile_count": 1,
  "event_count": 0,
  "memories": [
    {
      "id": "user_user123_1234567890.123",
      "action": "ignore",
      "layer": "profile",
      "reason": "这条记忆与现有记忆完全相同，无需重复存储",
      "status": "success"
    }
  ]
}
```

### 查询记忆的操作日志

```bash
curl "http://localhost:8000/memory/user_user123_1234567890.123/logs"
```

**响应**：
```json
{
  "memory_id": "user_user123_1234567890.123",
  "count": 2,
  "logs": [
    {
      "id": "log_abc123",
      "action": "insert",
      "reason": "插入新的profile层记忆",
      "created_at": "2026-01-09T12:00:00"
    },
    {
      "id": "log_def456",
      "action": "ignore",
      "reason": "这条记忆与现有记忆完全相同，无需重复存储",
      "created_at": "2026-01-09T12:05:00"
    }
  ]
}
```

### 手动更新（可指定原因）

```bash
curl -X PUT "http://localhost:8000/memory/user/user123/user_user123_1234567890.123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户是一名高级软件工程师，毕业于北京大学计算机系",
    "reason": "补充了具体的职级和学历专业"
  }'
```

## Why-Log 数据模型

```python
class MemoryLog(Base):
    id = Column(String, primary_key=True)
    memory_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # 'update', 'ignore', 'insert', 'delete'
    reason = Column(Text, nullable=False)  # 自然语言原因
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
```

## LLM 生成的 Why-Log 示例

### UPDATE 操作

```
原因 1: 新的信息更详细，包含了用户的职业背景
原因 2: 补充了具体的工作年限和所在公司
原因 3: 添加了用户的技能标签信息
```

### IGNORE 操作

```
原因 1: 这条记忆与现有记忆完全相同，无需重复存储
原因 2: 新记忆是现有记忆的子集，已包含在现有记忆中
原因 3: 这是临时对话内容，不具有长期保存价值
```

## Why-Log 的应用场景

### 1. 理解记忆变化

查看某条记忆的所有操作历史，了解它是如何变化的：

```bash
curl "http://localhost:8000/memory/user_user123_1234567890.123/logs?limit=20"
```

### 2. 优化抽取策略

分析大量的 ignore 日志，了解 LLM 为什么认为某些记忆不值得保存：

```bash
# 找出所有 ignore 的日志
curl -X POST "http://localhost:8000/memory/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "无价值的临时对话",
    "user_id": "user123",
    "top_k": 50
  }'
```

### 3. 优化提示词

根据日志反馈，调整 LLM 的提示词，提高判断准确性。

## Why-Log 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String | 日志唯一标识 |
| `memory_id` | String | 关联的记忆 ID |
| `action` | String | 操作类型：insert/update/ignore/delete |
| `reason` | Text | 自然语言原因说明 |
| `metadata` | JSON | 附加信息（如记忆层、更新字段等） |
| `created_at` | DateTime | 创建时间 |

## 自动抽取时的 Why-Log 流程

```
1. LLM 分析新内容和现有记忆
        ↓
2. LLM 决定操作类型（insert/update/ignore）
        ↓
3. LLM 生成自然语言原因
        ↓
4. 系统执行操作并记录日志
        ↓
5. 返回给用户（包含 reason 字段）
```

## 优势

### 1. 完全透明
所有自动操作都有原因说明，不再是黑盒。

### 2. 易于调试
当记忆处理不如预期时，可以通过日志快速定位问题。

### 3. 持续优化
可以通过分析日志持续改进 LLM 的决策质量。

### 4. 用户信任
用户可以理解系统的决策逻辑，增加信任度。

## 使用建议

1. **定期审查日志**：定期查看记忆日志，评估 LLM 的决策质量

2. **调整提示词**：根据日志反馈调整提取提示词

3. **监控关键词**：关注特定的关键词，如"重复"、"临时"、"无关"等

4. **统计指标**：统计 insert/update/ignore 的比例，评估抽取策略

5. **手动标注**：对于不确定的决策，可以手动添加更详细的原因
