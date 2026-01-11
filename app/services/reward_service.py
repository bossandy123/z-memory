from typing import List, Dict, Any, Optional
from app.core.reward import RewardCalculator
from app.core.rl_trainer import RLTrainer
from app.repositories.interfaces import ILogRepository


class RewardService:
    """奖励服务：RL 奖励计算和管理"""

    def __init__(self, log_repo: ILogRepository):
        self.log_repo = log_repo
        self.calculator = RewardCalculator()

    async def calculate(
        self,
        log_id: str,
        days_since_creation: int = 7
    ) -> Optional[Dict[str, Any]]:
        """计算奖励"""
        return await self.calculator.calculate_reward(
            log_id, days_since_creation
        )

    async def batch_evaluate(
        self,
        limit: int = 100,
        days_threshold: int = 7
    ) -> Dict[str, Any]:
        """批量评估奖励"""
        return await self.calculator.batch_evaluate_rewards(
            limit, days_threshold
        )

    async def get_statistics(
        self,
        action: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取奖励统计"""
        return await self.calculator.get_reward_statistics(
            action, days
        )


class TrainingService:
    """训练服务：RL 模型训练和管理"""

    def __init__(self):
        self.trainer = RLTrainer()

    async def train(
        self,
        days: int = 30,
        epochs: int = 10,
        save_checkpoint: bool = True
    ) -> Dict[str, Any]:
        """训练模型"""
        return await self.trainer.run_training_pipeline(
            days, epochs, save_checkpoint
        )

    async def get_training_samples(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取训练样本"""
        return await self.trainer.collect_training_samples(days)

    async def get_model_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取模型统计"""
        return await self.trainer.get_training_statistics(days)

    async def save_checkpoint(
        self,
        metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存模型检查点"""
        return await self.trainer.save_model_checkpoint(metrics)

    async def load_latest_model(
        self
    ) -> Optional[Dict[str, Any]]:
        """加载最新模型"""
        return await self.trainer.load_latest_model()
