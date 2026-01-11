from fastapi import APIRouter, HTTPException
from sqlalchemy import select, and_, func
from app.database.models import MemoryLog, async_session
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/memory")
async def get_memory_logs(
    memory_id: Optional[str] = None,
    memory_layer: Optional[str] = None,
    action: Optional[str] = None,
    skip_evaluated: Optional[bool] = False,
    limit: int = 20,
    offset: int = 0
):
    """获取记忆操作日志列表"""
    async with async_session() as session:
        query = select(MemoryLog)

        if memory_id:
            query = query.where(MemoryLog.memory_id == memory_id)
        if memory_layer:
            query = query.where(MemoryLog.memory_layer == memory_layer)
        if action:
            query = query.where(MemoryLog.action == action)
        if skip_evaluated:
            query = query.where(MemoryLog.reward.is_(None))

        total_query = select(func.count(MemoryLog.id))
        if memory_id:
            total_query = total_query.where(MemoryLog.memory_id == memory_id)
        if memory_layer:
            total_query = total_query.where(MemoryLog.memory_layer == memory_layer)
        if action:
            total_query = total_query.where(MemoryLog.action == action)
        if skip_evaluated:
            total_query = total_query.where(MemoryLog.reward.is_(None))

        total_result = await session.execute(total_query)
        total = total_result.scalar() or 0

        query = query.order_by(MemoryLog.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(query)
        logs = result.scalars().all()

        data = []
        for log in logs:
            data.append({
                "id": log.id,
                "memory_id": log.memory_id,
                "memory_layer": log.memory_layer,
                "action": log.action,
                "reason": log.reason,
                "metadata": log.meta_info,
                "reward": log.reward,
                "outcome": log.outcome,
                "evaluated_at": log.evaluated_at,
                "created_at": log.created_at,
            })

        return {"data": data, "total": total}


@router.get("/stats")
async def get_log_stats(days: int = 30):
    """获取日志统计信息"""
    async with async_session() as session:
        since = datetime.utcnow() - timedelta(days=days)

        total_query = select(func.count(MemoryLog.id)).where(MemoryLog.created_at >= since)
        total_result = await session.execute(total_query)
        total_logs = total_result.scalar() or 0

        evaluated_query = select(func.count(MemoryLog.id)).where(
            and_(
                MemoryLog.created_at >= since,
                MemoryLog.reward.isnot(None)
            )
        )
        evaluated_result = await session.execute(evaluated_query)
        evaluated_logs = evaluated_result.scalar() or 0

        pending_logs = max(0, total_logs - evaluated_logs) if total_logs else 0

        avg_reward_query = select(func.avg(MemoryLog.reward)).where(
            and_(
                MemoryLog.created_at >= since,
                MemoryLog.reward.isnot(None)
            )
        )
        avg_result = await session.execute(avg_reward_query)
        average_reward = avg_result.scalar() or 0.0

        action_query = select(
            MemoryLog.action,
            func.count(MemoryLog.id).label("count")
        ).where(MemoryLog.created_at >= since).group_by(MemoryLog.action)
        action_result = await session.execute(action_query)
        action_counts = {row[0]: row[1] for row in action_result}

        return {
            "total_logs": total_logs,
            "evaluated_logs": evaluated_logs,
            "pending_logs": pending_logs,
            "average_reward": average_reward,
            "action_counts": action_counts,
        }


@router.get("/{log_id}")
async def get_log_detail(log_id: str):
    """获取单条日志详情"""
    async with async_session() as session:
        query = select(MemoryLog).where(MemoryLog.id == log_id)
        result = await session.execute(query)
        log = result.scalar_one_or_none()

        if not log:
            raise HTTPException(status_code=404, detail="Log not found")

        return {
            "id": log.id,
            "memory_id": log.memory_id,
            "memory_layer": log.memory_layer,
            "action": log.action,
            "reason": log.reason,
            "metadata": log.meta_info,
            "reward": log.reward,
            "outcome": log.outcome,
            "evaluated_at": log.evaluated_at,
            "created_at": log.created_at,
        }
