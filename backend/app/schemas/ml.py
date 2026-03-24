from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ModelMetrics(BaseModel):
    model_version: str
    trained_at: datetime
    mae: float
    rmse: float
    r2: float
    feature_importances: Dict[str, float]
    training_samples: int
    validation_samples: int


class ComfortPredictionRequest(BaseModel):
    zone_id: int
    date: str
    hour: int
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    wind_gust: float
    cloud_cover: float
    pressure: float
    uv_index: Optional[float] = None
    fog: bool = False


class ComfortPredictionOut(BaseModel):
    zone_id: int
    date: str
    hour: int
    comfort_score: float
    confidence: Optional[float] = None
    contributing_factors: Dict[str, float]
