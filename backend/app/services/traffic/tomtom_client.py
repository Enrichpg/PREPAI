"""
TomTom Traffic API client.
Docs: https://developer.tomtom.com/traffic-api/traffic-api-documentation
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class TomTomTrafficClient:
    BASE_URL = settings.TOMTOM_BASE_URL

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TOMTOM_API_KEY
        self._client = httpx.AsyncClient()

    async def get_traffic_flow(self, bbox: str) -> Optional[Dict[str, Any]]:
        # bbox format: minLon,minLat,maxLon,maxLat
        url = f"{self.BASE_URL}/flowSegmentData/absolute/10/json"
        params = {
            "key": self.api_key,
            "bbox": bbox
        }
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
