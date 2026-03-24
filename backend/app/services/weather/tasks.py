"""Celery tasks for weather data ingestion."""
import asyncio
from datetime import date, timedelta
from loguru import logger
from app.core.celery_app import celery_app


@celery_app.task(name="app.services.weather.tasks.fetch_all_weather_data", bind=True, max_retries=3)
def fetch_all_weather_data(self):
    """Weekly task: fetch the last week of weather data from all sources."""
    from app.services.weather.ingestion import WeatherIngestionPipeline
    pipeline = WeatherIngestionPipeline()
    try:
        end = date.today()
        start = end - timedelta(days=8)  # overlap 1 day for safety
        result = asyncio.run(pipeline.ingest_aemet(start, end))
        logger.info(f"Weekly weather fetch complete: AEMET={result}")
        return {"aemet": result}
    except Exception as exc:
        logger.error(f"fetch_all_weather_data failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * 10)
    finally:
        pipeline.close()


@celery_app.task(name="app.services.weather.tasks.fetch_historical_weather", bind=True, max_retries=2)
def fetch_historical_weather(self, years: int = 10):
    """One-time historical backfill task."""
    from app.services.weather.ingestion import WeatherIngestionPipeline
    pipeline = WeatherIngestionPipeline()
    try:
        result = asyncio.run(pipeline.ingest_all(years=years))
        logger.info(f"Historical ingestion complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"fetch_historical_weather failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * 30)
    finally:
        pipeline.close()


@celery_app.task(name="app.services.weather.tasks.refresh_forecasts", bind=True, max_retries=3)
def refresh_forecasts(self):
    """Daily task: refresh weather forecasts for all zones."""
    from app.services.weather.ingestion import WeatherIngestionPipeline
    pipeline = WeatherIngestionPipeline()
    try:
        result = asyncio.run(pipeline.refresh_forecasts())
        logger.info(f"Forecast refresh complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"refresh_forecasts failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)
    finally:
        pipeline.close()
