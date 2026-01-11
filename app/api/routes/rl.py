from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.api.dependencies import container
from app.api.schemas.rl import (
    RewardCalculateRequest,
    RewardCalculateResponse,
    BatchRewardEvaluateRequest,
    TrainRequest,
    FeedbackRequest,
    RewardStatisticsResponse,
    TrainingSamplesResponse,
    ModelStatisticsResponse,
    SaveCheckpointResponse,
    LoadModelResponse,
    RLPipelineResponse,
    ExtractorStatisticsResponse,
    RLHealthResponse
)


router = APIRouter(prefix="/rl", tags=["RL Flywheel"])


@router.post("/reward/calculate", response_model=RewardCalculateResponse)
async def calculate_reward(
    request: RewardCalculateRequest,
    reward_service=Depends(lambda: container.reward_service)
):
    """
    计算单个日志的奖励

    - **log_id**: 日志ID
    - **days_since_creation**: 评估时间窗口（天）
    """
    result = await reward_service.calculate(
        request.log_id,
        request.days_since_creation
    )

    if not result:
        raise HTTPException(status_code=404, detail="Log not found")

    return RewardCalculateResponse(
        log_id=request.log_id,
        reward=result["reward"],
        outcome=result["outcome"],
        calculated_at=result["outcome"]["calculated_at"]
    )


@router.post("/reward/evaluate")
async def batch_evaluate_rewards(
    request: BatchRewardEvaluateRequest,
    reward_service=Depends(lambda: container.reward_service)
):
    """
    批量评估未计算的奖励

    - **limit**: 每次处理的最大数量
    - **days_threshold**: 只评估 N 天前的日志
    """
    result = await reward_service.batch_evaluate(
        limit=request.limit,
        days_threshold=request.days_threshold
    )

    return result


@router.get("/reward/statistics", response_model=RewardStatisticsResponse)
async def get_reward_statistics(
    action: Optional[str] = None,
    days: int = 30,
    reward_service=Depends(lambda: container.reward_service)
):
    """
    获取奖励统计信息

    - **action**: 操作类型过滤（可选）
    - **days**: 统计时间窗口
    """
    stats = await reward_service.get_statistics(action=action, days=days)

    return RewardStatisticsResponse(**stats)


@router.post("/train")
async def train_model(
    request: TrainRequest,
    training_service=Depends(lambda: container.training_service)
):
    """
    训练 RL 模型

    - **days**: 收集最近 N 天的数据
    - **epochs**: 训练轮数
    - **save_checkpoint**: 是否保存检查点
    """
    result = await training_service.train(
        days=request.days,
        epochs=request.epochs,
        save_checkpoint=request.save_checkpoint
    )

    return result


@router.get("/training/samples", response_model=TrainingSamplesResponse)
async def get_training_samples(
    days: int = 30,
    training_service=Depends(lambda: container.training_service)
):
    """
    获取训练样本

    - **days**: 收集最近 N 天的样本
    """
    samples = await training_service.get_training_samples(days=days)

    return TrainingSamplesResponse(
        count=len(samples),
        samples=samples[:100]
    )


@router.get("/model/checkpoints")
async def get_model_checkpoints(
    model_name: Optional[str] = None,
    version: Optional[str] = None,
    training_service=Depends(lambda: container.training_service)
):
    """
    获取模型检查点列表
    """
    from sqlalchemy import select
    from app.database.models import RLModelCheckpoint, async_session

    async with async_session() as session:
        query = select(RLModelCheckpoint)

        if model_name:
            query = query.where(RLModelCheckpoint.model_name == model_name)
        if version:
            query = query.where(RLModelCheckpoint.version == version)

        query = query.order_by(RLModelCheckpoint.created_at.desc())
        result = await session.execute(query)
        checkpoints = result.scalars().all()

        data = []
        for checkpoint in checkpoints:
            data.append({
                "id": checkpoint.id,
                "model_name": checkpoint.model_name,
                "version": checkpoint.version,
                "model_data": checkpoint.model_data,
                "metrics": checkpoint.metrics,
                "created_at": checkpoint.created_at.isoformat() if checkpoint.created_at else None,
            })

        return {"data": data, "total": len(data)}


@router.get("/model/checkpoint/{checkpoint_id}/download")
async def download_checkpoint(checkpoint_id: str):
    """
    下载检查点
    """
    from sqlalchemy import select
    from app.database.models import RLModelCheckpoint, async_session
    from fastapi.responses import JSONResponse

    async with async_session() as session:
        query = select(RLModelCheckpoint).where(RLModelCheckpoint.id == checkpoint_id)
        result = await session.execute(query)
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            raise HTTPException(status_code=404, detail="Checkpoint not found")

        return JSONResponse(content={
            "id": checkpoint.id,
            "model_name": checkpoint.model_name,
            "version": checkpoint.version,
            "model_data": checkpoint.model_data,
            "metrics": checkpoint.metrics,
        })


@router.get("/model/statistics", response_model=ModelStatisticsResponse)
async def get_model_statistics(
    days: int = 30,
    training_service=Depends(lambda: container.training_service)
):
    """
    获取模型统计信息

    - **days**: 统计时间窗口
    """
    stats = await training_service.get_model_statistics(days=days)

    return ModelStatisticsResponse(**stats)


@router.post("/model/save", response_model=SaveCheckpointResponse)
async def save_model_checkpoint(
    metrics: Optional[dict] = None,
    training_service=Depends(lambda: container.training_service)
):
    """
    保存当前模型检查点
    """
    checkpoint_id = await training_service.save_checkpoint(metrics=metrics)

    return SaveCheckpointResponse(
        checkpoint_id=checkpoint_id,
        message="Model checkpoint saved"
    )


@router.post("/model/load", response_model=LoadModelResponse)
async def load_latest_model(
    training_service=Depends(lambda: container.training_service)
):
    """
    加载最新的模型
    """
    model = await training_service.load_latest_model()

    if not model:
        raise HTTPException(status_code=404, detail="No model found")

    return LoadModelResponse(
        message="Model loaded successfully",
        model=model
    )


@router.post("/extractor/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    rl_extractor=Depends(lambda: container.rl_extractor)
):
    """
    提交反馈用于 RL 训练

    - **memory_id**: 记忆 ID
    - **actual_outcome**: 实际结果
    """
    result = await rl_extractor.feedback_loop(
        request.memory_id,
        request.actual_outcome
    )

    return result


@router.get("/extractor/statistics", response_model=ExtractorStatisticsResponse)
async def get_extractor_statistics(
    rl_extractor=Depends(lambda: container.rl_extractor)
):
    """
    获取 RL 抽取器统计信息
    """
    stats = await rl_extractor.get_rl_statistics()

    return ExtractorStatisticsResponse(**stats)


@router.get("/pipeline/run", response_model=RLPipelineResponse)
async def run_rl_pipeline(
    days: int = 7,
    train: bool = True,
    reward_service=Depends(lambda: container.reward_service),
    training_service=Depends(lambda: container.training_service)
):
    """
    运行完整的 RL 飞轮流程

    1. 批量评估奖励
    2. 收集训练样本
    3. 训练模型（如果启用）

    - **days**: 数据时间窗口
    - **train**: 是否训练模型
    """
    reward_result = await reward_service.batch_evaluate(
        limit=100,
        days_threshold=days
    )

    training_result = None
    if train:
        training_result = await training_service.train(
            days=days,
            epochs=5,
            save_checkpoint=True
        )

    return RLPipelineResponse(
        reward_evaluation=reward_result,
        training=training_result
    )


@router.get("/health", response_model=RLHealthResponse)
async def rl_health_check(
    training_service=Depends(lambda: container.training_service)
):
    """
    RL 飞轮健康检查
    """
    stats = await training_service.get_model_statistics(days=1)

    return RLHealthResponse(
        status="healthy",
        model_loaded=stats.model_version is not None,
        model_version=stats.model_version or "not loaded"
    )
