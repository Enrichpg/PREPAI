"""
Celery periodic task for continuous traffic ingestion and ML retraining.
"""
from app.services.traffic.traffic_ingestion import TrafficIngestionPipeline
from app.core.celery_app import celery_app
from app.services.ml.tasks import retrain_model

@celery_app.task(name="app.services.traffic.traffic_tasks.ingest_and_retrain", bind=True)
def ingest_and_retrain(self):
    # Example: A Coruña bbox and zone_id
    bbox = "-8.5,43.3,-8.3,43.4"
    zone_id = 1
    pipeline = TrafficIngestionPipeline()
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pipeline.ingest_traffic(bbox, zone_id))
    pipeline.close()
    retrain_model.delay()
