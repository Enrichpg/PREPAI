"""
Traffic ingestion pipeline for TomTom and other traffic APIs.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SyncSessionLocal
from app.services.traffic.tomtom_client import TomTomTrafficClient
from app.models.traffic import TrafficData

class TrafficIngestionPipeline:
    def __init__(self):
        self.db: Session = SyncSessionLocal()
        self.client = TomTomTrafficClient()

    async def ingest_traffic(self, bbox: str, zone_id: int):
        traffic_data = await self.client.get_traffic_flow(bbox)
        if not traffic_data:
            return {'inserted': 0}
        # Example: extract congestion index
        level = traffic_data.get('flowSegmentData', {}).get('currentSpeed', 0)
        description = traffic_data.get('flowSegmentData', {}).get('roadClosure', '')
        record = TrafficData(
            zone_id=zone_id,
            timestamp=datetime.utcnow(),
            traffic_level=level,
            description=description
        )
        self.db.add(record)
        self.db.commit()
        return {'inserted': 1}

    def close(self):
        self.db.close()
