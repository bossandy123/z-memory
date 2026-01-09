# Z-Memory 项目规范

## 目录结构规范

```
z-memory/
├── app/                    # 应用主目录
│   ├── main.py            # FastAPI 应用入口
│   ├── config.py          # 配置管理
│   ├── core/              # 核心业务逻辑
│   │   ├── memory.py      # 记忆管理模块
│   │   └── decision.py    # 决策层模块
│   ├── database/          # 数据库相关
│   │   ├── models.py      # SQLAlchemy 模型
│   │   └── vector_store.py # 向量存储
│   └── api/               # API 路由
│       └── routes/
│           ├── health.py  # 系统路由
│           ├── memory.py  # 记忆存储路由
│           └── query.py   # 查询路由
├── docs/                  # 文档
├── tests/                 # 测试代码
├── scripts/               # 工具脚本
└── .env.example           # 环境变量示例
```

## 代码规范

### 导入顺序

1. 标准库
2. 第三方库
3. 本地应用（从 app 开始）

```python
# 标准库
from typing import List, Dict, Any, Optional
from datetime import datetime

# 第三方库
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import select

# 本地应用
from app.core.memory import UserMemory, AgentMemory
from app.database.models import Memory
from app.config import settings
```

### 命名规范

- 类名：大驼峰命名法
- 函数/变量：小写+下划线
- 常量：全大写+下划线

### 文件职责

- `app/main.py` - FastAPI 应用初始化和中间件配置
- `app/config.py` - 配置管理（使用 pydantic-settings）
- `app/api/routes/health.py` - 健康检查和配置接口
- `app/api/routes/memory.py` - 记忆存储相关接口
- `app/api/routes/query.py` - 记忆查询接口
- `app/core/memory.py` - 记忆管理业务逻辑
- `app/core/decision.py` - 决策层逻辑
- `app/database/models.py` - 数据库模型定义
- `app/database/vector_store.py` - 向量存储封装

### API 设计规范

- 使用 RESTful 风格
- 路径使用小写+连字符（kebab-case）
- 返回统一的响应格式
- 使用 Pydantic 模型进行数据验证

### 测试规范

- 测试文件以 `test_` 开头
- 测试函数以 `test_` 开头
- 使用 pytest 框架
- 测试应该独立且可重复运行

### 配置管理

- 所有配置项通过 `app/config.py` 管理
- 敏感信息通过环境变量配置
- 配置文件示例：`.env.example`

### 目录说明

- `app/core/` - 核心业务逻辑（记忆管理、决策层）
- `app/database/` - 数据库相关（模型、向量存储）
- `app/api/routes/` - API 路由模块
  - `health.py` - 系统相关路由
  - `memory.py` - 记忆存储路由
  - `query.py` - 查询路由
- `app/main.py` - FastAPI 应用入口

## 启动命令

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 数据库初始化

```bash
python scripts/init_db.py
```
