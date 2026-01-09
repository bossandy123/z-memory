# 智能记忆抽取说明

## 功能概述

Z-Memory 的智能记忆抽取功能不仅能够从对话中提取重要信息，还能：

1. **获取现有记忆**：在抽取时参考已存储的记忆，避免重复
2. **智能去重**：自动识别完全相同的记忆并忽略
3. **智能更新**：识别可以合并或更新的现有记忆
4. **分类和优先级**：自动为记忆分类（偏好、决策、事件等）并评估重要性

## 工作流程

```
1. 用户调用自动抽取接口
        ↓
2. 系统获取该用户的现有记忆（最近50条）
        ↓
3. 将现有记忆作为上下文传递给 LLM
        ↓
4. LLM 分析新内容，决定每条记忆的操作类型：
   - insert: 插入新记忆
   - update: 更新现有记忆
   - ignore: 忽略重复记忆
        ↓
5. 系统根据操作类型执行相应操作
```

## 使用方式

### 自动抽取（推荐）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天告诉我他正在学习 Python 编程，并且打算以后从事 AI 开发工作。他还提到他喜欢开源项目，经常在 GitHub 上参与贡献。",
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
    {
      "id": "user_user123_0987654321.456",
      "action": "update",
      "status": "success",
      "updated_at": "2026-01-09T12:00:01"
    },
    {
      "id": "user_user123_5678901234.789",
      "action": "insert",
      "status": "success",
      "created_at": "2026-01-09T12:00:02"
    }
  ]
}
```

### 直接存储（不使用抽取）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户喜欢学习编程，特别是Python",
    "metadata": {"category": "preference"},
    "auto_extract": false
  }'
```

## LLM 的决策逻辑

LLM 会基于以下规则判断操作类型：

### 1. INSERT（插入新记忆）

当新抽取的记忆与现有记忆**完全不相关**或**内容完全不同**时：

```
现有记忆：
- 用户喜欢学习编程

新抽取的记忆：
- 用户喜欢吃苹果

操作：INSERT（全新记忆）
```

### 2. UPDATE（更新现有记忆）

当新抽取的记忆是现有记忆的**扩展、修正或细化**时：

```
现有记忆：
- 用户正在学习 Python

新抽取的记忆：
- 用户正在学习 Python 和 Go 语言

操作：UPDATE（扩展现有记忆）
```

```
现有记忆：
- 用户打算从事 AI 开发工作

新抽取的记忆：
- 用户打算从事 AI 开发，特别是自然语言处理方向

操作：UPDATE（细化现有记忆）
```

### 3. IGNORE（忽略重复记忆）

当新抽取的记忆与现有记忆**完全相同**或**含义基本一致**时：

```
现有记忆：
- 用户正在学习 Python 编程

新抽取的记忆：
- 用户正在学习 Python

操作：IGNORE（重复记忆）
```

## 记忆分类

LLM 会自动为每条记忆分类：

| 类型 | 说明 | 示例 |
|------|------|------|
| `preference` | 用户偏好 | 用户喜欢学习编程 |
| `decision` | 决策 | 用户决定使用 Python 开发项目 |
| `event` | 事件 | 用户昨天参加了技术会议 |
| `relationship` | 关系 | 用户是张伟的同事 |
| `other` | 其他 | 其他有价值的信息 |

## 重要性评估

LLM 会为每条记忆评分（1-5分）：

- **5分**：非常重要，长期保存
- **4分**：重要，需要长期关注
- **3分**：中等重要，一般保存
- **2分**：较低重要性
- **1分**：一般，边缘信息

## 优势

### 1. 避免重复存储

- 自动识别完全相同的记忆
- 避免存储冗余信息

### 2. 记忆一致性

- 通过更新保持记忆的最新状态
- 避免同一信息存在多个版本

### 3. 智能融合

- 能够将相关信息合并
- 保持记忆的完整性

### 4. 成本优化

- 减少不必要的存储操作
- 降低向量数据库的存储压力

## 配置要求

使用智能抽取功能需要配置 LLM：

```env
# LLM 配置
LLM_PROVIDER=dashscope  # 或 openai
LLM_MODEL=qwen-plus     # 或 gpt-4
LLM_TEMPERATURE=0.7      # 较低的温度更稳定

# 阿里云 DashScope
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_LLM_MODEL=qwen-plus

# 或 OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_LLM_MODEL=gpt-4
```

## 注意事项

1. **查询现有记忆**：每次自动抽取都会查询最近的 50 条记忆，会有一定的性能开销

2. **LLM 能力限制**：去重和更新的准确性依赖于 LLM 的理解能力

3. **上下文限制**：如果现有记忆过多，LLM 可能无法完全处理

4. **建议场景**：
   - ✅ 对话记录较少（< 1000 条）时使用自动抽取
   - ✅ 需要保证记忆一致性的场景
   - ❌ 大规模导入历史数据时使用直接存储

5. **成本考虑**：智能抽取会产生额外的 LLM 调用成本

## 调优建议

### 1. 调整查询数量

可以根据实际情况调整查询现有记忆的数量：

```python
# 在 memory.py 中调整
existing = await user_memory.query(user_id, "recent memories", top_k=100)  # 增加到100条
```

### 2. 调整温度参数

```env
LLM_TEMPERATURE=0.3  # 降低温度，使决策更稳定
```

### 3. 优化提示词

可以根据具体场景调整 `_build_extraction_prompt` 中的提示词
