"""
OpenWeatherMap API client.
Docs: https://openweathermap.org/api
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class OpenWeatherClient:
    BASE_URL = settings.OPENWEATHER_BASE_URL

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENWEATHER_API_KEY
        self._client = httpx.AsyncClient()

    async def get_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "es"
        }
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_forecast(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        url = f"{self.BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "es"
        }
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()
