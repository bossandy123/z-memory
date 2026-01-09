# API 路由文档

## 路由结构

Z-Memory API 使用模块化的路由设计，所有路由定义在 `app/api/routes/` 目录下。

## 路由模块

### System (`health.py`)

健康检查和系统配置相关路由。

#### 端点

- `GET /health` - 健康检查
- `GET /config` - 获取当前配置

### Memory (`memory.py`)

记忆管理相关路由（存储、更新、删除、查询）。

#### 端点

- `POST /memory/user/{user_id}` - 存储用户记忆
- `POST /memory/agent/{agent_id}` - 存储Agent记忆
- `PUT /memory/user/{user_id}/{memory_id}` - 更新用户记忆
- `PUT /memory/agent/{agent_id}/{memory_id}` - 更新Agent记忆
- `DELETE /memory/user/{user_id}/{memory_id}` - 删除用户记忆
- `DELETE /memory/agent/{agent_id}/{memory_id}` - 删除Agent记忆
- `GET /memory/{memory_id}` - 获取记忆详情

### Query (`query.py`)

记忆查询相关路由。

#### 端点

- `POST /memory/query` - 查询记忆（支持用户/Agent/混合查询）

## 请求模型

### MemoryRequest

用于创建新记忆。

```python
{
    "content": "记忆内容",
    "metadata": {"key": "value"},  // 可选
    "auto_extract": false          // 是否自动抽取，默认 false
}
```

### UpdateMemoryRequest

用于更新记忆。

```python
{
    "content": "新的记忆内容",    // 可选
    "metadata": {"key": "value"}  // 可选，至少提供 content 或 metadata 之一
}
```

### QueryRequest

```python
{
    "query": "查询内容",
    "user_id": "user123",        // 可选
    "agent_id": "agent001",      // 可选
    "top_k": 5                   // 默认5
}
```

### AgentProxyRequest

Agent 代理请求模型。

```python
{
    "content": "输入内容（如对话记录）",
    "mode": "auto|manual",       // 可选，不指定则使用配置
    "memories": [                // manual 模式下使用
        {
            "content": "记忆内容",
            "metadata": {"key": "value"}
        }
    ]
}
```

## 响应格式

### 存储记忆响应

**直接存储模式**：
```json
{
    "id": "user_user123_1234567890.123",
    "status": "success",
    "created_at": "2026-01-09T11:00:00",
    "mode": "direct"
}
```

**自动抽取模式（智能去重和更新）**：
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
            "created_at": "2026-01-09T11:00:00"
        },
        {
            "id": "user_user123_0987654321.456",
            "action": "update",
            "status": "success",
            "updated_at": "2026-01-09T11:01:00"
        }
    ]
}
```

### 更新记忆响应

```json
{
    "id": "user_user123_1234567890.123",
    "status": "success",
    "updated_at": "2026-01-09T12:00:00",
    "content": "更新后的内容",
    "metadata": {"key": "value"}
}
```

### 删除记忆响应

```json
{
    "id": "user_user123_1234567890.123",
    "status": "success",
    "message": "Memory deleted successfully"
}
```

### 查询记忆响应

```json
{
    "query": "查询内容",
    "results": {
        "user_memories": [...],
        "agent_memories": [...],
        "fused_context": [...],
        "recommendations": [...]
    }
}
```

### 获取记忆详情响应

```json
{
    "id": "user_user123_1234567890.123",
    "content": "记忆内容",
    "metadata": {"key": "value"},
    "created_at": "2026-01-09T11:00:00",
    "updated_at": "2026-01-09T11:00:00"
}
```

### 删除记忆响应

```json
{
    "id": "user_user123_1234567890.123",
    "status": "success",
    "message": "Memory deleted successfully"
}
```

## 错误处理

API 使用标准 HTTP 状态码：

- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源未找到
- `503` - 服务不可用（功能未启用）

## 路由注册

所有路由在 `app/api/__init__.py` 中通过 `register_routes` 函数统一注册到 FastAPI 应用。

```python
from app.api import register_routes

register_routes(app)
```

## 添加新路由

1. 在 `app/api/routes/` 创建新文件
2. 定义 `APIRouter` 实例
3. 在 `app/api/__init__.py` 中导入并注册

```python
# app/api/routes/example.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example_endpoint():
    return {"message": "Example"}

# app/api/__init__.py
from app.api.routes import example

def register_routes(app: FastAPI):
    app.include_router(example.router, tags=["Example"])
```
