from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from app.database.models import MemoryLog, ProfileMemory, EventMemory, async_session
import uuid


class RewardCalculator:
    """奖励计算器：根据记忆使用情况评估操作奖励"""

    def __init__(self, hit_weight: float = 1.0, quality_weight: float = 0.5,
                 time_decay_factor: float = 0.95):
        """
        初始化奖励计算器

        Args:
            hit_weight: 查询命中权重
            quality_weight: 质量提升权重
            time_decay_factor: 时间衰减因子
        """
        self.hit_weight = hit_weight
        self.quality_weight = quality_weight
        self.time_decay_factor = time_decay_factor

    async def calculate_reward(
        self,
        log_id: str,
        days_since_creation: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        计算指定日志的奖励

        Args:
            log_id: 日志ID
            days_since_creation: 评估的时间窗口（天）

        Returns:
            包含 reward 和 outcome 的字典
        """
        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog).where(MemoryLog.id == log_id)
            )
            log = result.scalar_one_or_none()

            if not log:
                return None

            memory_id = log.memory_id
            action = log.action
            created_at = log.created_at
            time_window = created_at + timedelta(days=days_since_creation)

            outcome = {}

            if action == "insert":
                reward = await self._calculate_insert_reward(
                    session, memory_id, created_at, time_window
                )
                outcome["evaluation_type"] = "insert"
            elif action == "update":
                reward = await self._calculate_update_reward(
                    session, memory_id, created_at, time_window
                )
                outcome["evaluation_type"] = "update"
            elif action == "ignore":
                reward = await self._calculate_ignore_reward(
                    session, memory_id, created_at, time_window
                )
                outcome["evaluation_type"] = "ignore"
            elif action == "delete":
                reward = await self._calculate_delete_reward(
                    session, memory_id, created_at, time_window
                )
                outcome["evaluation_type"] = "delete"
            else:
                return None

            outcome["time_window_days"] = days_since_creation
            outcome["calculated_at"] = datetime.utcnow().isoformat()

            log.reward = reward
            log.outcome = outcome
            log.evaluated_at = datetime.utcnow()
            await session.commit()

            return {"reward": reward, "outcome": outcome}

    async def _calculate_insert_reward(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> float:
        """计算 insert 操作的奖励"""
        reward = 0.0

        reward += await self._get_query_hit_reward(
            session, memory_id, created_at, time_window
        )

        time_passed = (datetime.utcnow() - created_at).days
        decay = self.time_decay_factor ** (time_passed / 7)
        reward *= decay

        return reward

    async def _calculate_update_reward(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> float:
        """计算 update 操作的奖励"""
        reward = 0.0

        hit_reward = await self._get_query_hit_reward(
            session, memory_id, created_at, time_window
        )
        reward += hit_reward * self.hit_weight

        quality_improvement = await self._get_quality_improvement(
            session, memory_id, created_at, time_window
        )
        reward += quality_improvement * self.quality_weight

        time_passed = (datetime.utcnow() - created_at).days
        decay = self.time_decay_factor ** (time_passed / 7)
        reward *= decay

        return reward

    async def _calculate_ignore_reward(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> float:
        """计算 ignore 操作的奖励"""
        reward = 0.0

        similar_memories = await self._get_similar_memories_count(
            session, memory_id, created_at, time_window
        )
        if similar_memories > 0:
            reward += 0.5 * similar_memories

        return reward

    async def _calculate_delete_reward(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> float:
        """计算 delete 操作的奖励"""
        reward = 0.0

        result = await session.execute(
            select(MemoryLog).where(
                MemoryLog.id == memory_id
            )
        )
        log = result.scalar_one_or_none()

        if log and log.action in ["insert", "update"]:
            recent_queries = await self._get_query_hit_reward(
                session, memory_id, created_at, time_window
            )
            if recent_queries < 0.1:
                reward += 0.5
            else:
                reward -= 0.3

        return reward

    async def _get_query_hit_reward(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> float:
        """获取查询命中奖励"""
        reward = 0.0

        result = await session.execute(
            select(func.count()).select_from(
                select(MemoryLog).where(
                    and_(
                        MemoryLog.memory_id == memory_id,
                        MemoryLog.action == "query",
                        MemoryLog.created_at >= created_at,
                        MemoryLog.created_at <= time_window
                    )
                ).subquery()
            )
        )
        query_count = result.scalar() or 0

        reward = query_count * self.hit_weight

        return reward

    async def _get_quality_improvement(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> float:
        """获取质量提升奖励"""
        improvement = 0.0

        async with async_session() as profile_session:
            profile_result = await profile_session.execute(
                select(ProfileMemory).where(ProfileMemory.id == memory_id)
            )
            profile = profile_result.scalar_one_or_none()

            if profile and profile.meta_info:
                improvement += profile.meta_info.get("quality_score", 0) * 0.5

        async with async_session() as event_session:
            event_result = await event_session.execute(
                select(EventMemory).where(EventMemory.id == memory_id)
            )
            event = event_result.scalar_one_or_none()

            if event and event.meta_info:
                improvement += event.meta_info.get("quality_score", 0) * 0.5

        return improvement

    async def _get_similar_memories_count(
        self,
        session,
        memory_id: str,
        created_at: datetime,
        time_window: datetime
    ) -> int:
        """获取相似记忆数量"""
        return 0

    async def batch_evaluate_rewards(
        self,
        limit: int = 100,
        days_threshold: int = 7
    ) -> Dict[str, Any]:
        """
        批量评估未计算的奖励

        Args:
            limit: 每次处理的最大数量
            days_threshold: 只评估 N 天前的日志

        Returns:
            评估结果统计
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)

        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog).where(
                    and_(
                        MemoryLog.evaluated_at.is_(None),
                        MemoryLog.created_at < threshold_date,
                        MemoryLog.action.in_(["insert", "update", "ignore", "delete"])
                    )
                ).limit(limit)
            )
            logs = result.scalars().all()

        total = len(logs)
        successful = 0
        failed = 0
        total_reward = 0.0

        for log in logs:
            try:
                result = await self.calculate_reward(log.id, days_threshold)
                if result:
                    successful += 1
                    total_reward += result["reward"]
                else:
                    failed += 1
            except Exception as e:
                failed += 1

        return {
            "total_evaluated": total,
            "successful": successful,
            "failed": failed,
            "average_reward": total_reward / successful if successful > 0 else 0,
            "total_reward": total_reward
        }

    async def get_reward_statistics(
        self,
        action: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取奖励统计信息

        Args:
            action: 操作类型过滤
            days: 统计时间窗口

        Returns:
            统计信息
        """
        threshold_date = datetime.utcnow() - timedelta(days=days)

        async with async_session() as session:
            query = select(func.count(), func.avg(MemoryLog.reward), func.stddev(MemoryLog.reward)).where(
                and_(
                    MemoryLog.reward.isnot(None),
                    MemoryLog.evaluated_at >= threshold_date
                )
            )

            if action:
                query = query.where(MemoryLog.action == action)

            result = await session.execute(query)
            count, avg_reward, stddev_reward = result.one()

            return {
                "action": action or "all",
                "count": count or 0,
                "average_reward": float(avg_reward) if avg_reward else 0,
                "stddev_reward": float(stddev_reward) if stddev_reward else 0,
                "time_window_days": days
            }
