"""
Event ingestion pipeline for Eventbrite and other event APIs.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SyncSessionLocal
from app.services.events.eventbrite_client import EventbriteClient
from app.models.events import Event
from app.models.zones import Zone

class EventIngestionPipeline:
    def __init__(self):
        self.db: Session = SyncSessionLocal()
        self.client = EventbriteClient()

    async def ingest_events(self, lat: float, lon: float, radius_km: int = 10):
        events_data = await self.client.search_events(lat, lon, radius_km)
        inserted = 0
        for event in events_data.get('events', []):
            zone = self._find_zone(lat, lon)
            db_event = Event(
                external_id=event['id'],
                name=event['name']['text'],
                start_time=datetime.fromisoformat(event['start']['utc']),
                end_time=datetime.fromisoformat(event['end']['utc']),
                zone_id=zone.id if zone else None,
                venue=event['venue']['name'] if event.get('venue') else None,
                latitude=event['venue']['latitude'] if event.get('venue') else lat,
                longitude=event['venue']['longitude'] if event.get('venue') else lon,
            )
            self.db.add(db_event)
            inserted += 1
        self.db.commit()
        return {'inserted': inserted}

    def _find_zone(self, lat, lon):
        # Dummy implementation, replace with spatial query
        return self.db.query(Zone).first()

    def close(self):
        self.db.close()
