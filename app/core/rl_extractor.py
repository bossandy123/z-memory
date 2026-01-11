from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.agent import MemoryExtractor
from app.core.rl_trainer import RLTrainer
from app.core.reward import RewardCalculator
from app.database.models import MemoryLog, async_session
from sqlalchemy import select
import uuid


class RLEnhancedExtractor:
    """RL 增强的记忆抽取器：结合 LLM 和 RL 策略"""

    def __init__(self, enable_rl: bool = True, rl_temperature: float = 0.5):
        """
        初始化 RL 增强抽取器

        Args:
            enable_rl: 是否启用 RL 策略
            rl_temperature: RL 预测的温度参数
        """
        self.memory_extractor = MemoryExtractor()
        self.rl_trainer = RLTrainer()
        self.enable_rl = enable_rl
        self.rl_temperature = rl_temperature

        if enable_rl:
            import asyncio
            asyncio.create_task(self._load_model())

    async def _load_model(self):
        """加载最新的 RL 模型"""
        try:
            await self.rl_trainer.load_latest_model()
        except Exception:
            pass

    async def extract_memories(
        self,
        content: str,
        entity_id: str,
        entity_type: str = "user",
        existing_memories: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        从内容中抽取记忆（RL 增强版本）

        Args:
            content: 输入内容（如对话记录）
            entity_id: 实体 ID（user_id 或 agent_id）
            entity_type: 实体类型（user 或 agent）
            existing_memories: 现有的记忆列表（用于去重和更新判断）

        Returns:
            抽取到的记忆列表，每个记忆包含操作类型和原因
        """
        llm_memories = await self.memory_extractor.extract_memories(
            content, entity_id, existing_memories
        )

        if not self.enable_rl:
            return llm_memories

        rl_enhanced_memories = []
        for mem in llm_memories:
            rl_action = await self._predict_rl_action(mem, entity_type)
            enhanced_mem = self._enhance_with_rl(mem, rl_action)
            rl_enhanced_memories.append(enhanced_mem)

        return rl_enhanced_memories

    async def _predict_rl_action(
        self,
        memory: Dict[str, Any],
        entity_type: str
    ) -> Optional[str]:
        """
        使用 RL 模型预测最优操作

        Args:
            memory: LLM 抽取的记忆
            entity_type: 实体类型

        Returns:
            RL 预测的操作类型
        """
        state = await self._build_state(memory, entity_type)
        rl_action = self.rl_trainer.predict_action(state, self.rl_temperature)

        return rl_action

    async def _build_state(
        self,
        memory: Dict[str, Any],
        entity_type: str
    ) -> Dict[str, Any]:
        """构建 RL 状态特征"""
        metadata = memory.get("metadata", {})

        return {
            "memory_layer": memory.get("memory_layer", "event"),
            "importance_score": metadata.get("importance", 3),
            "memory_type": metadata.get("memory_type", "other"),
            "content_features": {
                "length": len(memory.get("content", "")),
                "category": metadata.get("category", "unknown")
            },
            "temporal_features": {
                "is_recent": True,
                "days_ago": 0
            },
            "llm_action": memory.get("action", "insert")
        }

    def _enhance_with_rl(
        self,
        original_memory: Dict[str, Any],
        rl_action: Optional[str]
    ) -> Dict[str, Any]:
        """
        用 RL 预测结果增强记忆

        Args:
            original_memory: 原始 LLM 抽取的记忆
            rl_action: RL 预测的操作

        Returns:
            增强后的记忆
        """
        enhanced = original_memory.copy()

        if rl_action and rl_action != original_memory.get("action"):
            enhanced["original_llm_action"] = original_memory.get("action")
            enhanced["action"] = rl_action
            enhanced["reason"] = self._combine_reasons(
                original_memory.get("reason", ""),
                f"RL 策略建议改为 {rl_action}"
            )
            enhanced["rl_enhanced"] = True
        else:
            enhanced["rl_enhanced"] = False

        return enhanced

    def _combine_reasons(self, llm_reason: str, rl_reason: str) -> str:
        """合并 LLM 和 RL 的原因"""
        return f"{llm_reason} {rl_reason}"

    async def extract_with_ensemble(
        self,
        content: str,
        entity_id: str,
        entity_type: str = "user",
        existing_memories: List[Dict[str, Any]] = None,
        confidence_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        使用集成策略抽取记忆

        Args:
            content: 输入内容
            entity_id: 实体 ID
            entity_type: 实体类型
            existing_memories: 现有记忆
            confidence_threshold: 置信度阈值

        Returns:
            抽取到的记忆列表
        """
        llm_memories = await self.memory_extractor.extract_memories(
            content, entity_id, existing_memories
        )

        if not self.enable_rl:
            return llm_memories

        ensemble_memories = []
        for mem in llm_memories:
            rl_action = await self._predict_rl_action(mem, entity_type)

            confidence = self._calculate_ensemble_confidence(
                mem.get("action", "insert"),
                rl_action,
                mem.get("importance", 3)
            )

            if confidence >= confidence_threshold:
                ensemble_mem = self._select_action(mem, rl_action, confidence)
            else:
                ensemble_mem = mem.copy()
                ensemble_mem["confidence"] = confidence

            ensemble_memories.append(ensemble_mem)

        return ensemble_memories

    def _calculate_ensemble_confidence(
        self,
        llm_action: str,
        rl_action: Optional[str],
        importance: int
    ) -> float:
        """计算集成置信度"""
        if not rl_action:
            return 0.6

        if llm_action == rl_action:
            base_confidence = 0.9
        else:
            base_confidence = 0.5

        importance_factor = (importance - 3) * 0.1

        confidence = base_confidence + importance_factor
        confidence = max(0.1, min(0.95, confidence))

        return confidence

    def _select_action(
        self,
        memory: Dict[str, Any],
        rl_action: str,
        confidence: float
    ) -> Dict[str, Any]:
        """选择最终的操作"""
        if confidence >= 0.8:
            selected_action = memory.get("action", "insert")
        else:
            selected_action = rl_action

        enhanced = memory.copy()
        enhanced["action"] = selected_action
        enhanced["confidence"] = confidence
        enhanced["rl_action"] = rl_action
        enhanced["llm_action"] = memory.get("action", "insert")

        if selected_action != memory.get("action", "insert"):
            enhanced["reason"] = self._combine_reasons(
                memory.get("reason", ""),
                f"RL 覆盖（置信度：{confidence:.2f}）"
            )
            enhanced["rl_overridden"] = True
        else:
            enhanced["rl_overridden"] = False

        return enhanced

    async def feedback_loop(
        self,
        memory_id: str,
        actual_outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        反馈循环：记录实际结果用于 RL 训练

        Args:
            memory_id: 记忆 ID
            actual_outcome: 实际结果

        Returns:
            反馈结果
        """
        from app.database.models import MemoryLog, async_session
        from sqlalchemy import select

        async with async_session() as session:
            result = await session.execute(
                select(MemoryLog).where(MemoryLog.memory_id == memory_id)
            ).order_by(MemoryLog.created_at.desc()).limit(1)
            log = result.scalar_one_or_none()

            if not log:
                return {"success": False, "error": "Log not found"}

            if log.reward is None:
                from app.core.reward import RewardCalculator
                calculator = RewardCalculator()
                reward_result = await calculator.calculate_reward(log.id)
                if reward_result:
                    return {
                        "success": True,
                        "reward_calculated": True,
                        "reward": reward_result["reward"],
                        "outcome": reward_result["outcome"]
                    }

            return {
                "success": True,
                "reward_calculated": False,
                "existing_reward": log.reward,
                "message": "Reward already calculated"
            }

    async def get_rl_statistics(self) -> Dict[str, Any]:
        """获取 RL 统计信息"""
        if not self.enable_rl:
            return {
                "enabled": False,
                "message": "RL is not enabled"
            }

        return {
            "enabled": True,
            "temperature": self.rl_temperature,
            "model_version": self.rl_trainer.model_weights.get("version"),
            "action_preferences": self.rl_trainer.model_weights.get("action_preferences", {})
        }
