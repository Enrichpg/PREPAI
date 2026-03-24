"""
Eventbrite API client.
Docs: https://www.eventbrite.com/platform/api
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class EventbriteClient:
    BASE_URL = settings.EVENTBRITE_BASE_URL

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.EVENTBRITE_API_KEY
        self._client = httpx.AsyncClient(headers={"Authorization": f"Bearer {self.api_key}"})

    async def search_events(self, lat: float, lon: float, radius_km: int = 10, q: Optional[str] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/events/search/"
        params = {
            "location.latitude": lat,
            "location.longitude": lon,
            "location.within": f"{radius_km}km",
            "expand": "venue"
        }
        if q:
            params["q"] = q
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
