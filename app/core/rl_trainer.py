from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, and_, func
from app.database.models import MemoryLog, RLTrainingSample, RLModelCheckpoint, async_session
from app.core.reward import RewardCalculator
import uuid
import json
import numpy as np


class RLTrainer:
    """强化学习训练器：从 Why-Log 中训练记忆抽取策略"""

    ACTIONS = ["insert", "update", "ignore", "delete"]

    def __init__(self, model_name: str = "memory_policy"):
        """
        初始化训练器

        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self.reward_calculator = RewardCalculator()
        self.model_weights = self._init_model_weights()

    def _init_model_weights(self) -> Dict[str, Any]:
        """初始化模型权重"""
        return {
            "action_preferences": {
                "insert": 0.5,
                "update": 0.3,
                "ignore": 0.15,
                "delete": 0.05
            },
            "feature_weights": {
                "content_length": 0.1,
                "similarity_threshold": 0.2,
                "importance_score": 0.3,
                "recency_factor": 0.2,
                "memory_layer_weight": 0.2
            },
            "version": "1.0",
            "trained_at": None
        }

    async def collect_training_samples(
        self,
        days: int = 30,
        min_reward: float = -10.0,
        max_reward: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        从 Why-Log 中收集训练样本

        Args:
            days: 收集最近 N 天的数据
            min_reward: 最小奖励过滤
            max_reward: 最大奖励过滤

        Returns:
            训练样本列表
        """
        threshold_date = datetime.utcnow() - timedelta(days=days)

        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog).where(
                    and_(
                        MemoryLog.reward.isnot(None),
                        MemoryLog.evaluated_at >= threshold_date,
                        MemoryLog.reward >= min_reward,
                        MemoryLog.reward <= max_reward
                    )
                )
            )
            logs = result.scalars().all()

        samples = []
        for log in logs:
            try:
                sample = await self._create_training_sample(log)
                if sample:
                    samples.append(sample)
            except Exception as e:
                continue

        return samples

    async def _create_training_sample(
        self,
        log: MemoryLog
    ) -> Optional[Dict[str, Any]]:
        """从日志创建训练样本"""
        state = await self._extract_state(log)

        return {
            "log_id": log.id,
            "entity_id": log.meta_info.get("entity_id", "unknown"),
            "entity_type": log.meta_info.get("memory_type", "unknown"),
            "state": state,
            "action": log.action,
            "reward": float(log.reward),
            "done": False
        }

    async def _extract_state(
        self,
        log: MemoryLog
    ) -> Dict[str, Any]:
        """提取状态特征"""
        meta_info = log.meta_info or {}

        return {
            "memory_layer": log.memory_layer,
            "previous_actions": await self._get_previous_actions(log.memory_id, limit=5),
            "action_frequency": await self._get_action_frequency(log.memory_id),
            "content_features": self._extract_content_features(meta_info),
            "temporal_features": self._extract_temporal_features(log.created_at),
            "importance_score": meta_info.get("importance", 3),
            "memory_type": meta_info.get("memory_type", "other")
        }

    async def _get_previous_actions(
        self,
        memory_id: str,
        limit: int = 5
    ) -> List[str]:
        """获取之前的操作序列"""
        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog.action).where(
                    MemoryLog.memory_id == memory_id
                ).order_by(MemoryLog.created_at.desc()).limit(limit)
            )
            return list(result.scalars().all())[::-1]

    async def _get_action_frequency(
        self,
        memory_id: str
    ) -> Dict[str, int]:
        """获取操作频率统计"""
        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog.action, func.count(MemoryLog.id)).where(
                    MemoryLog.memory_id == memory_id
                ).group_by(MemoryLog.action)
            )

            freq = {action: 0 for action in self.ACTIONS}
            for action, count in result.all():
                freq[action] = count

            return freq

    def _extract_content_features(
        self,
        meta_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取内容特征"""
        return {
            "has_category": "category" in meta_info,
            "has_source": "source" in meta_info,
            "category": meta_info.get("category", "unknown"),
            "source": meta_info.get("source", "unknown"),
            "is_auto_extracted": meta_info.get("auto_extracted", False)
        }

    def _extract_temporal_features(
        self,
        created_at: datetime
    ) -> Dict[str, Any]:
        """提取时间特征"""
        now = datetime.utcnow()
        days_ago = (now - created_at).days

        return {
            "days_ago": days_ago,
            "is_recent": days_ago < 7,
            "is_month_old": days_ago < 30
        }

    async def save_training_samples(
        self,
        samples: List[Dict[str, Any]]
    ) -> int:
        """
        保存训练样本到数据库

        Args:
            samples: 训练样本列表

        Returns:
            保存的数量
        """
        count = 0
        async with async_session() as session:
            for sample in samples:
                training_sample = RLTrainingSample(
                    id=str(uuid.uuid4()),
                    log_id=sample["log_id"],
                    entity_id=sample["entity_id"],
                    entity_type=sample["entity_type"],
                    state=sample["state"],
                    action=sample["action"],
                    reward=sample["reward"],
                    next_state=None,
                    done=sample["done"]
                )
                session.add(training_sample)
                count += 1
            await session.commit()

        return count

    def train(
        self,
        samples: List[Dict[str, Any]],
        epochs: int = 10,
        learning_rate: float = 0.01
    ) -> Dict[str, Any]:
        """
        训练模型（简化版：基于统计学习）

        Args:
            samples: 训练样本
            epochs: 训练轮数
            learning_rate: 学习率

        Returns:
            训练结果
        """
        if not samples:
            return {"success": False, "error": "No samples provided"}

        for epoch in range(epochs):
            action_rewards = {action: [] for action in self.ACTIONS}

            for sample in samples:
                action = sample["action"]
                reward = sample["reward"]
                action_rewards[action].append(reward)

            for action in self.ACTIONS:
                if action_rewards[action]:
                    avg_reward = np.mean(action_rewards[action])
                    self.model_weights["action_preferences"][action] = (
                        self.model_weights["action_preferences"][action] * (1 - learning_rate) +
                        avg_reward * learning_rate
                    )

            self._normalize_action_preferences()

        self.model_weights["version"] = str(
            float(self.model_weights["version"]) + 0.1
        )
        self.model_weights["trained_at"] = datetime.utcnow().isoformat()

        return {
            "success": True,
            "epochs": epochs,
            "samples": len(samples),
            "model_weights": self.model_weights
        }

    def _normalize_action_preferences(self):
        """归一化操作偏好"""
        total = sum(self.model_weights["action_preferences"].values())
        if total > 0:
            for action in self.ACTIONS:
                self.model_weights["action_preferences"][action] /= total

    async def save_model_checkpoint(
        self,
        metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        保存模型检查点

        Args:
            metrics: 模型指标

        Returns:
            检查点ID
        """
        checkpoint = RLModelCheckpoint(
            id=str(uuid.uuid4()),
            model_name=self.model_name,
            version=self.model_weights["version"],
            model_data=self.model_weights,
            metrics=metrics or {}
        )

        async with async_session() as session:
            session.add(checkpoint)
            await session.commit()

        return checkpoint.id

    async def load_latest_model(
        self
    ) -> Optional[Dict[str, Any]]:
        """加载最新的模型"""
        async with async_session() as session:
            result = await session.execute(
                select(RLModelCheckpoint).where(
                    RLModelCheckpoint.model_name == self.model_name
                ).order_by(RLModelCheckpoint.created_at.desc()).limit(1)
            )
            checkpoint = result.scalar_one_or_none()

            if checkpoint:
                self.model_weights = checkpoint.model_data
                return checkpoint.model_data

            return None

    def predict_action(
        self,
        state: Dict[str, Any],
        temperature: float = 0.5
    ) -> str:
        """
        预测最优操作

        Args:
            state: 状态特征
            temperature: 温度参数（控制随机性）

        Returns:
            预测的操作
        """
        base_preferences = self.model_weights["action_preferences"].copy()

        importance = state.get("importance_score", 3)
        if importance >= 4:
            base_preferences["insert"] *= 1.2
            base_preferences["update"] *= 1.1
        elif importance <= 2:
            base_preferences["ignore"] *= 1.2

        is_recent = state.get("temporal_features", {}).get("is_recent", False)
        if is_recent:
            base_preferences["ignore"] *= 1.1

        total = sum(base_preferences.values())
        if total > 0:
            base_preferences = {k: v / total for k, v in base_preferences.items()}

        if temperature > 0:
            preferences = {k: v ** (1 / temperature) for k, v in base_preferences.items()}
            total = sum(preferences.values())
            probabilities = {k: v / total for k, v in preferences.items()}
        else:
            probabilities = base_preferences

        actions = list(probabilities.keys())
        probs = list(probabilities.values())

        chosen_action = np.random.choice(actions, p=probs)

        return chosen_action

    async def run_training_pipeline(
        self,
        days: int = 30,
        epochs: int = 10,
        save_checkpoint: bool = True
    ) -> Dict[str, Any]:
        """
        运行完整的训练流程

        Args:
            days: 收集最近 N 天的数据
            epochs: 训练轮数
            save_checkpoint: 是否保存检查点

        Returns:
            训练结果
        """
        result = {
            "success": True,
            "samples_collected": 0,
            "samples_saved": 0,
            "training_metrics": None,
            "checkpoint_id": None
        }

        samples = await self.collect_training_samples(days=days)
        result["samples_collected"] = len(samples)

        if not samples:
            return {
                **result,
                "success": False,
                "error": "No training samples collected"
            }

        saved_count = await self.save_training_samples(samples)
        result["samples_saved"] = saved_count

        training_result = self.train(samples, epochs=epochs)
        result["training_metrics"] = training_result

        if save_checkpoint and training_result["success"]:
            checkpoint_id = await self.save_model_checkpoint({
                "samples_count": len(samples),
                "epochs": epochs,
                "average_reward": np.mean([s["reward"] for s in samples])
            })
            result["checkpoint_id"] = checkpoint_id

        return result

    async def get_training_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取训练统计信息"""
        threshold_date = datetime.utcnow() - timedelta(days=days)

        async with async_session() as session:
            sample_count_result = await session.execute(
                select(func.count(RLTrainingSample.id)).where(
                    RLTrainingSample.created_at >= threshold_date
                )
            )
            sample_count = sample_count_result.scalar() or 0

            avg_reward_result = await session.execute(
                select(func.avg(RLTrainingSample.reward)).where(
                    RLTrainingSample.created_at >= threshold_date
                )
            )
            avg_reward = avg_reward_result.scalar() or 0

            checkpoint_count_result = await session.execute(
                select(func.count(RLModelCheckpoint.id)).where(
                    RLModelCheckpoint.model_name == self.model_name
                )
            )
            checkpoint_count = checkpoint_count_result.scalar() or 0

        return {
            "model_name": self.model_name,
            "model_version": self.model_weights.get("version"),
            "samples_count_last_30_days": sample_count,
            "average_reward": float(avg_reward) if avg_reward else 0,
            "checkpoints_count": checkpoint_count,
            "current_weights": self.model_weights
        }


from datetime import timedelta
