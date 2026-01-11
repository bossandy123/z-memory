import pytest
from app.core.reward import RewardCalculator
from app.core.rl_trainer import RLTrainer
from app.core.rl_extractor import RLEnhancedExtractor
from app.database.models import MemoryLog, async_session
from datetime import datetime, timedelta
import uuid


@pytest.mark.asyncio
async def test_reward_calculator_initialization():
    """测试奖励计算器初始化"""
    calculator = RewardCalculator()
    assert calculator.hit_weight == 1.0
    assert calculator.quality_weight == 0.5
    assert calculator.time_decay_factor == 0.95


@pytest.mark.asyncio
async def test_reward_calculator_custom_weights():
    """测试自定义权重"""
    calculator = RewardCalculator(
        hit_weight=2.0,
        quality_weight=1.0,
        time_decay_factor=0.9
    )
    assert calculator.hit_weight == 2.0
    assert calculator.quality_weight == 1.0
    assert calculator.time_decay_factor == 0.9


@pytest.mark.asyncio
async def test_calculate_reward_nonexistent_log():
    """测试计算不存在的日志奖励"""
    calculator = RewardCalculator()
    result = await calculator.calculate_reward("nonexistent_log_id")
    assert result is None


@pytest.mark.asyncio
async def test_reward_statistics():
    """测试获取奖励统计信息"""
    calculator = RewardCalculator()
    stats = await calculator.get_reward_statistics(days=30)
    assert "action" in stats
    assert "count" in stats
    assert "average_reward" in stats
    assert stats["count"] >= 0


@pytest.mark.asyncio
async def test_reward_statistics_with_action_filter():
    """测试按操作类型过滤统计"""
    calculator = RewardCalculator()
    stats = await calculator.get_reward_statistics(action="insert", days=30)
    assert stats["action"] == "insert"


@pytest.mark.asyncio
async def test_batch_evaluate_rewards():
    """测试批量评估奖励"""
    calculator = RewardCalculator()
    result = await calculator.batch_evaluate_rewards(limit=10, days_threshold=7)
    assert "total_evaluated" in result
    assert "successful" in result
    assert "failed" in result
    assert "average_reward" in result


@pytest.mark.asyncio
async def test_rl_trainer_initialization():
    """测试 RL 训练器初始化"""
    trainer = RLTrainer()
    assert trainer.model_name == "memory_policy"
    assert "action_preferences" in trainer.model_weights
    assert "feature_weights" in trainer.model_weights


@pytest.mark.asyncio
async def test_rl_trainer_custom_model_name():
    """测试自定义模型名称"""
    trainer = RLTrainer(model_name="custom_model")
    assert trainer.model_name == "custom_model"


@pytest.mark.asyncio
async def test_collect_training_samples():
    """测试收集训练样本"""
    trainer = RLTrainer()
    samples = await trainer.collect_training_samples(days=30)
    assert isinstance(samples, list)


@pytest.mark.asyncio
async def test_train_model():
    """测试训练模型"""
    trainer = RLTrainer()

    samples = [
        {
            "log_id": str(uuid.uuid4()),
            "entity_id": "test_entity",
            "entity_type": "user",
            "state": {
                "memory_layer": "event",
                "importance_score": 3,
                "memory_type": "other"
            },
            "action": "insert",
            "reward": 1.0,
            "done": False
        }
    ]

    result = trainer.train(samples, epochs=1, learning_rate=0.01)
    assert result["success"] is True
    assert "model_weights" in result


@pytest.mark.asyncio
async def test_train_model_empty_samples():
    """测试使用空样本训练模型"""
    trainer = RLTrainer()
    result = trainer.train([], epochs=1)
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_save_model_checkpoint():
    """测试保存模型检查点"""
    trainer = RLTrainer()
    checkpoint_id = await trainer.save_model_checkpoint(
        metrics={"test": "value"}
    )
    assert checkpoint_id is not None


@pytest.mark.asyncio
async def test_predict_action():
    """测试预测操作"""
    trainer = RLTrainer()

    state = {
        "memory_layer": "event",
        "importance_score": 3,
        "memory_type": "other",
        "temporal_features": {
            "is_recent": True,
            "days_ago": 0
        },
        "llm_action": "insert"
    }

    action = trainer.predict_action(state, temperature=0.5)
    assert action in trainer.ACTIONS


@pytest.mark.asyncio
async def test_get_training_statistics():
    """测试获取训练统计信息"""
    trainer = RLTrainer()
    stats = await trainer.get_training_statistics(days=30)
    assert "model_name" in stats
    assert "samples_count_last_30_days" in stats
    assert "average_reward" in stats


@pytest.mark.asyncio
async def test_rl_extractor_initialization():
    """测试 RL 抽取器初始化"""
    extractor = RLEnhancedExtractor()
    assert extractor.enable_rl is True
    assert extractor.rl_temperature == 0.5


@pytest.mark.asyncio
async def test_rl_extractor_disabled():
    """测试禁用 RL"""
    extractor = RLEnhancedExtractor(enable_rl=False)
    assert extractor.enable_rl is False


@pytest.mark.asyncio
async def test_build_state():
    """测试构建 RL 状态"""
    extractor = RLEnhancedExtractor()

    memory = {
        "content": "测试记忆",
        "action": "insert",
        "memory_layer": "event",
        "metadata": {
            "importance": 3,
            "memory_type": "other"
        }
    }

    state = await extractor._build_state(memory, "user")
    assert "memory_layer" in state
    assert "importance_score" in state
    assert "memory_type" in state


@pytest.mark.asyncio
async def test_calculate_ensemble_confidence():
    """测试计算集成置信度"""
    extractor = RLEnhancedExtractor()

    confidence = extractor._calculate_ensemble_confidence(
        llm_action="insert",
        rl_action="insert",
        importance=3
    )
    assert 0 <= confidence <= 1

    confidence_low = extractor._calculate_ensemble_confidence(
        llm_action="insert",
        rl_action="ignore",
        importance=1
    )
    assert 0 <= confidence_low <= 1


@pytest.mark.asyncio
async def test_enhance_with_rl():
    """测试 RL 增强"""
    extractor = RLEnhancedExtractor()

    original_memory = {
        "content": "测试记忆",
        "action": "insert",
        "reason": "LLM 原因"
    }

    enhanced = extractor._enhance_with_rl(original_memory, "update")
    assert enhanced["original_llm_action"] == "insert"
    assert enhanced["action"] == "update"
    assert enhanced["rl_enhanced"] is True


@pytest.mark.asyncio
async def test_select_action():
    """测试选择操作"""
    extractor = RLEnhancedExtractor()

    memory = {
        "content": "测试记忆",
        "action": "insert",
        "reason": "LLM 原因"
    }

    selected = extractor._select_action(memory, "update", 0.5)
    assert selected["action"] in ["insert", "update"]
    assert "confidence" in selected
    assert "rl_action" in selected
    assert "llm_action" in selected


@pytest.mark.asyncio
async def test_get_rl_statistics():
    """测试获取 RL 统计信息"""
    extractor = RLEnhancedExtractor()
    stats = await extractor.get_rl_statistics()
    assert "enabled" in stats
    if stats["enabled"]:
        assert "temperature" in stats
        assert "model_version" in stats


@pytest.mark.asyncio
async def test_run_training_pipeline():
    """测试运行训练流程"""
    trainer = RLTrainer()

    result = await trainer.run_training_pipeline(
        days=30,
        epochs=1,
        save_checkpoint=False
    )
    assert "success" in result
    assert "samples_collected" in result
