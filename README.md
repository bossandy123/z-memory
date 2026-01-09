# Z-Memory

智能记忆管理系统，支持用户记忆、Agent记忆和智能决策层。

## 架构设计

```
┌─────────────┐     ┌─────────────┐
│  User API   │     │ Agent API   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  Decision Layer  │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │   Memory Core    │
        └────────┬─────────┘
                 │
        ┌─────────▼──────────┐
        │                    │
 ┌──────▼──────┐     ┌──────▼──────┐
 │ PostgreSQL  │     │   Qdrant    │
 │ (元数据存储) │     │ (向量搜索)   │
 └─────────────┘     └─────────────┘
```

## 特性

- **双存储架构**：PostgreSQL 存储结构化数据 + Qdrant 存储向量嵌入
- **语义搜索**：支持 OpenAI 或阿里云 DashScope 的高精度语义匹配
- **智能融合**：决策层自动融合和排序多源记忆
- **灵活配置**：支持单独启用 User/Agent 记忆或同时启用
- **类型隔离**：用户记忆和 Agent 记忆独立管理
- **完整管理**：支持记忆的创建、查询、更新、删除
- **RESTful API**：完整的 REST API 接口

## 配置模式

支持三种配置模式：

### 1. 只启用 User 记忆
```env
ENABLE_USER_MEMORY=true
ENABLE_AGENT_MEMORY=false
```

### 2. 只启用 Agent 记忆
```env
ENABLE_USER_MEMORY=false
ENABLE_AGENT_MEMORY=true
```

### 3. 同时启用（默认）
```env
ENABLE_USER_MEMORY=true
ENABLE_AGENT_MEMORY=true
```

## 快速开始

### 1. 启动依赖服务

```bash
docker-compose up -d
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

选择配置模式，复制对应的配置文件：

```bash
# 模式1: 只启用 User 记忆
cp .env.user_only .env

# 或模式2: 只启用 Agent 记忆
cp .env.agent_only .env

# 或模式3: 同时启用（默认）
cp .env.both .env
```

编辑 `.env`，填入你的 API Key：
```bash
# 填入阿里云 DashScope API Key
DASHSCOPE_API_KEY=your-dashscope-api-key-here
```

### 4. 初始化数据库

```bash
python scripts/init_db.py
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档

### 验证配置

```bash
curl http://localhost:8000/config
```

## API 使用示例

### 查看当前配置

```bash
curl http://localhost:8000/config
```

### 存储用户记忆（需启用 ENABLE_USER_MEMORY）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户喜欢学习编程，特别是Python",
    "metadata": {"category": "preference", "source": "conversation"}
  }'
```

### 更新用户记忆

```bash
curl -X PUT "http://localhost:8000/memory/user/user123/user_user123_1234567890.123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户更喜欢学习Python和Go语言",
    "metadata": {"category": "preference", "updated": true}
  }'
```

### 删除用户记忆

```bash
curl -X DELETE "http://localhost:8000/memory/user/user123/user_user123_1234567890.123"
```

### 存储Agent记忆（需启用 ENABLE_AGENT_MEMORY）

```bash
curl -X POST "http://localhost:8000/memory/agent/agent001" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户在第3次对话中提到了对AI的兴趣",
    "metadata": {"category": "insight", "importance": "high"}
  }'
```

### 查询记忆

```bash
# 同时查询用户和Agent记忆
curl -X POST "http://localhost:8000/memory/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户对什么感兴趣",
    "user_id": "user123",
    "agent_id": "agent001",
    "top_k": 5
  }'

# 只查询用户记忆
curl -X POST "http://localhost:8000/memory/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "用户的偏好是什么",
    "user_id": "user123",
    "top_k": 5
  }'

# 只查询Agent记忆
curl -X POST "http://localhost:8000/memory/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "关于用户的洞察",
    "agent_id": "agent001",
    "top_k": 5
  }'
```

## 项目结构

```
z-memory/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI 主入口
│   ├── config.py          # 配置管理
│   ├── core/              # 核心业务逻辑
│   │   ├── memory.py      # 记忆管理
│   │   └── decision.py    # 决策层
│   ├── database/          # 数据库相关
│   │   ├── models.py      # SQLAlchemy 模型
│   │   └── vector_store.py # Qdrant 向量存储
│   └── api/               # API 路由
│       └── routes/
│           ├── health.py  # 健康检查和配置
│           ├── memory.py  # 记忆管理路由
│           └── query.py   # 查询路由
├── docs/                  # 文档
│   ├── INSTALLATION.md    # 安装说明
│   ├── CONFIGURATION.md   # 详细配置说明
│   ├── DEVELOPMENT.md     # 开发规范
│   └── API.md             # API 文档
├── tests/                 # 测试
│   ├── conftest.py        # 测试配置
│   └── test_api.py        # API 测试
├── scripts/               # 脚本
│   └── init_db.py         # 数据库初始化
├── requirements.txt        # Python 依赖
├── docker-compose.yml      # Docker 编排
├── .env.example           # 环境变量示例
├── .env.user_only         # 用户记忆模式配置
├── .env.agent_only        # Agent 记忆模式配置
└── .env.both              # 双模式配置
```

## 技术栈

- **API**: FastAPI
- **数据库**: PostgreSQL 16 (异步连接)
- **向量库**: Qdrant 1.7.0
- **Embeddings**: 阿里云 DashScope text-embedding-v2 (支持 OpenAI 备选)
- **ORM**: SQLAlchemy 2.0 (异步)
- **测试**: Pytest

## 运行测试

```bash
pytest tests/ -v
```

## 开发说明

### 代码规范

- 所有应用代码位于 `app/` 目录下
- 测试代码位于 `tests/` 目录下
- 工具脚本位于 `scripts/` 目录下

### 目录说明

- `app/core/` - 核心业务逻辑（记忆管理、决策层）
- `app/database/` - 数据库相关（模型、向量存储）
- `app/api/` - API 路由模块
- `app/main.py` - FastAPI 应用入口

## 更多文档

- [安装说明](docs/INSTALLATION.md)
- [配置说明](docs/CONFIGURATION.md)
- [开发规范](docs/DEVELOPMENT.md)
- [API 文档](docs/API.md)
