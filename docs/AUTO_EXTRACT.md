# 自动抽取功能说明

## 概述

Z-Memory 提供了智能自动抽取功能，使用 LLM 从对话内容中智能提取重要的记忆信息。

## 智能特性

### 1. 参考现有记忆
在抽取时，系统会先获取该用户/Agent的现有记忆作为上下文，确保 LLM 了解已存储的内容。

### 2. 智能去重
自动识别完全相同的记忆并标记为忽略，避免重复存储。

### 3. 智能更新
识别可以合并或更新的现有记忆，自动执行更新操作。

### 4. 智能分类
自动为每条记忆分类（偏好、决策、事件、关系等）并评估重要性。

## 工作流程

```
输入内容 → 查询现有记忆 → LLM 抽取和决策 → 执行操作
                    ↓
            [insert/update/ignore]
```

## 使用方式

### 自动抽取（推荐）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天告诉我他正在学习 Python 编程，并且打算以后从事 AI 开发工作。",
    "auto_extract": true
  }'
```

**响应示例**：
```json
{
  "mode": "auto_extract",
  "total_extracted": 3,
  "inserted": 2,
  "updated": 1,
  "ignored": 0,
  "memories": [
    {
      "id": "user_user123_1234567890.123",
      "action": "insert",
      "status": "success",
      "created_at": "2026-01-09T12:00:00"
    },
    ...
  ]
}
```

### 直接存储（不使用抽取）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户喜欢学习编程",
    "metadata": {"category": "preference"},
    "auto_extract": false
  }'
```

## 操作类型说明

| 操作类型 | 说明 | 场景 |
|---------|------|------|
| `insert` | 插入新记忆 | 全新信息 |
| `update` | 更新现有记忆 | 扩展、修正或细化 |
| `ignore` | 忽略重复记忆 | 完全相同或含义一致 |

## 适用场景

### 使用自动抽取 (`auto_extract: true`)

- ✅ 从对话记录中提取信息
- ✅ 需要避免重复存储
- ✅ 需要保持记忆一致性
- ✅ 对话记录较少（< 1000 条）

### 使用直接存储 (`auto_extract: false`)

- ✅ 已知要存储的具体内容
- ✅ 需要精确控制记忆内容
- ✅ 大规模导入历史数据
- ✅ 成本敏感

## 配置要求

使用自动抽取功能需要配置 LLM：

```env
# LLM 配置（用于自动抽取记忆）
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus
LLM_TEMPERATURE=0.7

# 阿里云 DashScope
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_LLM_MODEL=qwen-plus

# 或 OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_LLM_MODEL=gpt-4
```

## 详细说明

更多详细信息请参考：
- [智能抽取详细说明](docs/SMART_EXTRACT.md) - 完整的工作流程和决策逻辑
