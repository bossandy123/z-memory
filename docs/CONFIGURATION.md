# 配置模式说明

## 模式1: 只启用 User 记忆

适用于只需要管理用户记忆的场景，如：
- 个人知识管理工具
- 用户偏好记录系统
- 用户历史对话存储

**配置文件 (`.env`):**
```env
ENABLE_USER_MEMORY=true
ENABLE_AGENT_MEMORY=false
```

**可用端点:**
- `POST /memory/user/{user_id}` - 存储用户记忆
- `GET /memory/{memory_id}` - 查询记忆
- `POST /memory/query` - 查询记忆（仅支持 user_id）
- `GET /config` - 查看配置

**不可用端点:**
- `POST /memory/agent/{agent_id}` - 端点不存在

---

## 模式2: 只启用 Agent 记忆

适用于只需要管理Agent记忆的场景，如：
- Agent 学习系统
- 多Agent协作平台
- Agent 经验库

**配置文件 (`.env`):**
```env
ENABLE_USER_MEMORY=false
ENABLE_AGENT_MEMORY=true
```

**可用端点:**
- `POST /memory/agent/{agent_id}` - 存储Agent记忆
- `POST /memory/query` - 查询记忆（仅支持 agent_id）
- `GET /config` - 查看配置

**不可用端点:**
- `POST /memory/user/{user_id}` - 端点不存在
- `GET /memory/{memory_id}` - 端点不存在

---

## 模式3: 同时启用（默认模式）

适用于需要同时管理用户和Agent记忆的场景，如：
- 智能对话系统
- 个性化AI助手
- 多角色交互平台

**配置文件 (`.env`):**
```env
ENABLE_USER_MEMORY=true
ENABLE_AGENT_MEMORY=true
```

**可用端点:**
- `POST /memory/user/{user_id}` - 存储用户记忆
- `POST /memory/agent/{agent_id}` - 存储Agent记忆
- `GET /memory/{memory_id}` - 查询记忆
- `POST /memory/query` - 查询记忆（支持 user_id 和 agent_id）
- `GET /config` - 查看配置

---

## 注意事项

1. **至少需要启用一个记忆模块**，否则启动时会报错
2. 切换配置后需要重启服务
3. 查询时会自动验证请求参数与配置是否匹配
