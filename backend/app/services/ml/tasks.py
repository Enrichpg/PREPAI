"""Celery tasks for ML model training."""
from loguru import logger
from app.core.celery_app import celery_app


@celery_app.task(name="app.services.ml.tasks.retrain_model", bind=True, max_retries=2)
def retrain_model(self):
    """Weekly task: retrain the comfort model with fresh data."""
    from app.db.database import SyncSessionLocal
    from app.services.ml.comfort_model import ComfortModel

    db = SyncSessionLocal()
    try:
        model = ComfortModel()
        metrics = model.train(db)
        logger.info(f"Model retrained successfully: {metrics}")
        return metrics
    except Exception as exc:
        logger.error(f"Model retraining failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * 15)
    finally:
        db.close()


@celery_app.task(name="app.services.ml.tasks.update_forecast_comfort_scores")
def update_forecast_comfort_scores():
    """Update comfort scores in weather_forecasts table using the current model."""
    from app.db.database import SyncSessionLocal
    from app.services.ml.comfort_model import get_comfort_model
    from app.models.weather import WeatherForecast
    from sqlalchemy import select
    import pandas as pd

    db = SyncSessionLocal()
    model = get_comfort_model()
    updated = 0
    try:
        forecasts = db.execute(
            select(WeatherForecast).where(WeatherForecast.comfort_score.is_(None))
        ).scalars().all()

        if not forecasts:
            return {"updated": 0}

        rows = []
        for f in forecasts:
            rows.append({
                "id": f.id,
                "temperature": f.temperature,
                "humidity": f.humidity,
                "precipitation": f.precipitation,
                "precipitation_probability": f.precipitation_probability,
                "wind_speed": f.wind_speed,
                "wind_gust": f.wind_gust,
                "cloud_cover": f.cloud_cover,
                "pressure": f.pressure,
                "uv_index": f.uv_index,
                "solar_radiation": None,
                "fog": f.fog,
                "hour": f.forecast_for.hour,
                "month": f.forecast_for.month,
                "visibility": None,
            })

        df = pd.DataFrame(rows)
        scores = model.predict(df.drop(columns=["id"]))

        for forecast, score in zip(forecasts, scores):
            forecast.comfort_score = float(score)
        db.commit()
        updated = len(forecasts)
        logger.info(f"Updated {updated} forecast comfort scores")
    except Exception as e:
        logger.error(f"update_forecast_comfort_scores failed: {e}")
        db.rollback()
    finally:
        db.close()

    return {"updated": updated}
