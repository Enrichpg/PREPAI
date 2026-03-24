"""
Celery periodic task for continuous Eventbrite ingestion and ML retraining.
"""
from app.services.events.event_ingestion import EventIngestionPipeline
from app.core.celery_app import celery_app
from app.services.ml.tasks import retrain_model

@celery_app.task(name="app.services.events.event_tasks.ingest_and_retrain", bind=True)
def ingest_and_retrain(self):
    # Example: A Coruña coordinates
    lat, lon, radius_km = 43.37017285554117, -8.400987452390712, 30
    pipeline = EventIngestionPipeline()
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pipeline.ingest_events(lat, lon, radius_km))
    pipeline.close()
    retrain_model.delay()
