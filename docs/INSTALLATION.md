# 安装说明

## 前置要求

- Python 3.8+
- Docker (用于 PostgreSQL 和 Qdrant)

## 安装步骤

### 1. 克隆项目

```bash
cd z-memory
```

### 2. 启动依赖服务

```bash
docker-compose up -d
```

### 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

选择配置模式并复制配置文件：

```bash
# 模式1: 只启用 User 记忆
cp .env.user_only .env

# 或模式2: 只启用 Agent 记忆
cp .env.agent_only .env

# 或模式3: 同时启用（默认）
cp .env.both .env
```

编辑 `.env` 文件，填入必要的 API Key：

```bash
# 如果使用阿里云 DashScope
DASHSCOPE_API_KEY=your-dashscope-api-key-here

# 如果使用 OpenAI
OPENAI_API_KEY=your-openai-api-key-here
EMBEDDING_PROVIDER=openai
```

### 5. 初始化数据库

```bash
python scripts/init_db.py
```

如果看到 `Database tables created successfully!` 说明数据库初始化成功。

### 6. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，访问：
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 7. 验证安装

```bash
curl http://localhost:8000/health
curl http://localhost:8000/config
```

## 常见问题

### ModuleNotFoundError: No module named 'app'

确保在项目根目录运行命令，或者使用：

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/init_db.py
```

### ModuleNotFoundError: No module named 'dashscope'

确保已安装依赖：

```bash
pip install -r requirements.txt
```

### 连接数据库失败

确保 Docker 服务正在运行：

```bash
docker-compose ps
```

如果需要重启服务：

```bash
docker-compose restart
```

### Qdrant 连接失败

检查 Qdrant 是否运行：

```bash
curl http://localhost:6333/
```

应该返回 Qdrant 的版本信息。
