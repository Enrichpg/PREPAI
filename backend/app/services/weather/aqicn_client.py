"""
AQICN Air Quality API client.
Docs: https://aqicn.org/api/
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class AQICNClient:
    BASE_URL = settings.AQICN_BASE_URL

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.AQICN_API_KEY
        self._client = httpx.AsyncClient()

    async def get_air_quality(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/feed/geo:{lat};{lon}/"
        params = {"token": self.api_key}
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
