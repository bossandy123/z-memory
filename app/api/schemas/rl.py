from pydantic import BaseModel
from typing import Optional, Dict, Any


class RewardCalculateRequest(BaseModel):
    log_id: str
    days_since_creation: int = 7


class RewardCalculateResponse(BaseModel):
    log_id: str
    reward: Optional[float]
    outcome: Optional[dict]
    calculated_at: str


class BatchRewardEvaluateRequest(BaseModel):
    limit: int = 100
    days_threshold: int = 7


class TrainRequest(BaseModel):
    days: int = 30
    epochs: int = 10
    save_checkpoint: bool = True


class FeedbackRequest(BaseModel):
    memory_id: str
    actual_outcome: dict


class RewardStatisticsResponse(BaseModel):
    action: str
    count: int
    average_reward: float
    stddev_reward: float
    time_window_days: int


class TrainingSamplesResponse(BaseModel):
    count: int
    samples: list


class ModelStatisticsResponse(BaseModel):
    model_name: str
    model_version: Optional[str]
    samples_count_last_30_days: int
    average_reward: float
    checkpoints_count: int
    current_weights: Dict[str, Any]


class SaveCheckpointResponse(BaseModel):
    checkpoint_id: str
    message: str


class LoadModelResponse(BaseModel):
    message: str
    model: Optional[Dict[str, Any]]


class RLPipelineResponse(BaseModel):
    reward_evaluation: Optional[Dict[str, Any]]
    training: Optional[Dict[str, Any]]


class ExtractorStatisticsResponse(BaseModel):
    enabled: bool
    temperature: Optional[float] = None
    model_version: Optional[str] = None
    action_preferences: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class RLHealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
