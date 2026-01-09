# Z-Memory

智能记忆管理系统，支持用户记忆、Agent记忆、智能决策层和记忆分层管理。

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
         │                  │
         │  ├── 分层管理    │
         │  ├── 智能抽取    │
         │  └── Why-Log     │
         └────────┬─────────┘
                 │
        ┌─────────▼──────────┐
        │                    │
 ┌──────▼──────┐     ┌──────▼──────┐
 │ PostgreSQL  │     │   Qdrant    │
 │ (记忆+日志) │     │ (向量搜索)   │
 └─────────────┘     └─────────────┘
```

## 特性

- **双存储架构**：PostgreSQL 存储结构化数据 + Qdrant 存储向量嵌入
- **语义搜索**：支持 OpenAI 或阿里云 DashScope 的高精度语义匹配
- **智能融合**：决策层自动融合和排序多源记忆
- **灵活配置**：支持单独启用 User/Agent 记忆或同时启用
- **类型隔离**：用户记忆和 Agent 记忆独立管理
- **完整管理**：支持记忆的创建、查询、更新、删除
- **智能抽取**：支持 LLM 自动从对话中提取记忆（包含去重和更新）
- **记忆分层**：Profile 层（画像）+ Event 层（事件）清晰分离
- **Why-Log**：自动记录操作原因，透明可追溯
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

## 记忆分层

### Profile 层（画像层）
记录长期、稳定的信息：性格、能力、职业、学历、偏好等

### Event 层（事件层）
记录动态事件和行为：对话记录、日常行为、具体事件等

## Why-Log（操作日志）

在 Auto 模式下自动记录操作原因：

- **INSERT**: 插入新记忆的原因
- **UPDATE**: 更新现有记忆的原因  
- **IGNORE**: 忽略重复记忆的原因

### 查询日志

```bash
curl "http://localhost:8000/memory/{memory_id}/logs"
```

详细说明请参考 [Why-Log 文档](docs/WHY_LOG.md)

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
# 填入阿里云 DashScope API Key（用于 Embedding 和 LLM）
DASHSCOPE_API_KEY=your-dashscope-api-key-here

# 如果使用 OpenAI
OPENAI_API_KEY=your-openai-api-key-here
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
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

### 存储用户记忆（指定记忆层）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户喜欢学习编程，特别是Python",
    "metadata": {"category": "preference", "source": "conversation"},
    "memory_layer": "profile",
    "is_permanent": true
  }'
```

### 自动抽取（智能去重、更新和 Why-Log）

```bash
curl -X POST "http://localhost:8000/memory/user/user123" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "用户今天告诉我他正在学习 Python 编程，并且打算以后从事 AI 开发工作。他还提到他喜欢开源项目，经常在 GitHub 上参与贡献。不过他昨天也说过他正在学习 Python。",
    "auto_extract": true
  }'
```

**响应示例**：
```json
{
  "mode": "auto_extract",
  "total_extracted": 2,
  "inserted": 1,
  "updated": 1,
  "ignored": 1,
  "profile_count": 1,
  "event_count": 1,
  "memories": [
    {
      "id": "user_user123_1234567890.123",
      "action": "insert",
      "layer": "profile",
      "reason": "这是新的用户职业规划信息",
      "status": "success"
    },
    {
      "id": "user_user123_0987654321.456",
      "action": "update",
      "layer": "profile",
      "reason": "新的信息更详细，补充了用户的职业背景",
      "status": "success"
    },
    {
      "id": "user_user123_5678901234.789",
      "action": "ignore",
      "layer": "profile",
      "reason": "这条记忆与现有记忆完全相同，无需重复存储",
      "status": "success"
    }
  ]
}
```

### 查询操作日志

```bash
curl "http://localhost:8000/memory/user_user123_1234567890.123/logs"
```

### 查询分层记忆

```bash
# 获取用户画像（Profile 层）
curl "http://localhost:8000/memory/user/user123/profile"

# 获取用户事件（Event 层）
curl "http://localhost:8000/memory/user/user123/events?limit=50"
```

更多 API 示例请参考 [API 文档](docs/API.md)

## 项目结构

```
z-memory/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI 主入口
│   ├── config.py          # 配置管理
│   ├── core/              # 核心业务逻辑
│   │   ├── memory.py      # 记忆管理 + 日志记录
│   │   ├── agent.py       # 记忆抽取
│   │   └── decision.py    # 决策层
│   ├── database/          # 数据库相关
│   │   ├── models.py      # SQLAlchemy 模型（包含 MemoryLog）
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
│   ├── API.md             # API 文档
│   ├── AUTO_EXTRACT.md    # 自动抽取概述
│   ├── SMART_EXTRACT.md   # 智能抽取详细说明
│   ├── MEMORY_LAYERS.md   # 记忆分层说明
│   └── SEPARATE_LAYERS.md  # 分表详细说明
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

- `app/core/` - 核心业务逻辑（记忆管理、抽取、决策层）
- `app/database/` - 数据库相关（模型、向量存储）
- `app/api/` - API 路由模块
- `app/main.py` - FastAPI 应用入口

## 更多文档

- [安装说明](docs/INSTALLATION.md)
- [配置说明](docs/CONFIGURATION.md)
- [开发规范](docs/DEVELOPMENT.md)
- [API 文档](docs/API.md)
- [自动抽取概述](docs/AUTO_EXTRACT.md)
- [智能抽取详细说明](docs/SMART_EXTRACT.md)
- [记忆分层说明](docs/MEMORY_LAYERS.md)
- [Why-Log 说明](docs/WHY_LOG.md)
