# 记忆分层概述

## 记忆层次

Z-Memory 支持记忆分层管理：

### 1. Profile 层（画像层）
- 记录长期、稳定的信息
- 如：性格、能力、职业、学历、偏好等

### 2. Event 层（事件层）
- 记录动态事件和行为
- 如：对话记录、日常行为、具体事件等

## Why-Log（操作日志）

在 Auto 模式下自动记录操作原因：

- **INSERT**: 插入新记忆的原因
- **UPDATE**: 更新现有记忆的原因
- **IGNORE**: 忽略重复记忆的原因

### 查询日志

```bash
curl "http://localhost:8000/memory/{memory_id}/logs"
```

详细说明请参考：
- [记忆分层文档](docs/MEMORY_LAYERS.md)
- [Why-Log 文档](docs/WHY_LOG.md)
