from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from loguru import logger

from app.db.database import get_db
from app.schemas.ml import ModelMetrics, ComfortPredictionRequest, ComfortPredictionOut

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.get("/model/metrics", response_model=Optional[dict])
async def get_model_metrics():
    """Get current model performance metrics."""
    from app.services.ml.comfort_model import get_comfort_model
    model = get_comfort_model()
    metrics = model.get_metrics()
    if not metrics:
        return {"message": "Modelo no entrenado aún. Ejecuta el entrenamiento primero."}
    return {
        "version": model.version,
        "metrics": metrics,
    }


@router.post("/model/train")
async def trigger_training():
    """Manually trigger model retraining."""
    from app.services.ml.tasks import retrain_model
    task = retrain_model.delay()
    return {"task_id": task.id, "message": "Entrenamiento del modelo iniciado"}


@router.post("/predict/comfort", response_model=ComfortPredictionOut)
async def predict_comfort(request: ComfortPredictionRequest):
    """Predict running comfort score for given weather conditions."""
    from app.services.ml.comfort_model import get_comfort_model, engineer_features, FEATURE_COLUMNS
    import pandas as pd
    import numpy as np

    model = get_comfort_model()

    df = pd.DataFrame([{
        "temperature": request.temperature,
        "humidity": request.humidity,
        "precipitation": request.precipitation,
        "precipitation_probability": 0,
        "wind_speed": request.wind_speed,
        "wind_gust": request.wind_gust,
        "cloud_cover": request.cloud_cover,
        "pressure": request.pressure,
        "uv_index": request.uv_index or 0,
        "solar_radiation": None,
        "fog": float(request.fog),
        "hour": request.hour,
        "month": int(request.date[5:7]),
        "visibility": None,
    }])

    df_engineered = engineer_features(df)

    # Get feature importances for explanation
    feature_vals = df_engineered[FEATURE_COLUMNS].iloc[0].to_dict()
    contributing = {}
    if model.model is not None and hasattr(model.model, "feature_importances_"):
        importances = model.model.feature_importances_
        for feat, imp in zip(FEATURE_COLUMNS, importances):
            contributing[feat] = round(float(imp), 4)

    score = float(model.predict(df)[0])

    return ComfortPredictionOut(
        zone_id=request.zone_id,
        date=request.date,
        hour=request.hour,
        comfort_score=round(score, 1),
        contributing_factors=contributing,
    )
