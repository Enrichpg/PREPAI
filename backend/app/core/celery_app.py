from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "prepai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.weather.tasks",
        "app.services.ml.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
    task_routes={
        "app.services.weather.tasks.*": {"queue": "weather"},
        "app.services.ml.tasks.*": {"queue": "ml"},
    },
    beat_schedule={
        # Every Monday at 03:00 AM fetch new weather data
        "fetch-weekly-weather": {
            "task": "app.services.weather.tasks.fetch_all_weather_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=1),
            "options": {"queue": "weather"},
        },
        # After data fetch (Monday 06:00) retrain model
        "retrain-weekly-model": {
            "task": "app.services.ml.tasks.retrain_model",
            "schedule": crontab(hour=6, minute=0, day_of_week=1),
            "options": {"queue": "ml"},
        },
        # Daily forecast refresh at 05:00
        "refresh-daily-forecasts": {
            "task": "app.services.weather.tasks.refresh_forecasts",
            "schedule": crontab(hour=5, minute=0),
            "options": {"queue": "weather"},
        },
        # Hourly event ingestion and ML retraining
        "ingest-events-and-retrain": {
            "task": "app.services.events.event_tasks.ingest_and_retrain",
            "schedule": crontab(minute=0),
            "options": {"queue": "ml"},
        },
        # Hourly traffic ingestion and ML retraining
        "ingest-traffic-and-retrain": {
            "task": "app.services.traffic.traffic_tasks.ingest_and_retrain",
            "schedule": crontab(minute=0),
            "options": {"queue": "ml"},
        },
    },
)
