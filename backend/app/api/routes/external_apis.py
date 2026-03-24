from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.weather.openweather_client import OpenWeatherClient
from app.services.weather.aqicn_client import AQICNClient
from app.services.events.eventbrite_client import EventbriteClient
from app.services.traffic.tomtom_client import TomTomTrafficClient

router = APIRouter(prefix="/external", tags=["external-apis"])

@router.get("/weather/openweathermap")
async def get_openweather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """Get current weather from OpenWeatherMap."""
    client = OpenWeatherClient()
    try:
        data = await client.get_weather(lat, lon)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenWeatherMap error: {e}")
    finally:
        await client.close()

@router.get("/air/aqicn")
async def get_aqicn(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    """Get air quality from AQICN."""
    client = AQICNClient()
    try:
        data = await client.get_air_quality(lat, lon)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AQICN error: {e}")
    finally:
        await client.close()

@router.get("/events/eventbrite")
async def get_eventbrite(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(10, ge=1, le=100),
    q: Optional[str] = None
):
    """Search events from Eventbrite."""
    client = EventbriteClient()
    try:
        data = await client.search_events(lat, lon, radius_km, q)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Eventbrite error: {e}")
    finally:
        await client.close()

@router.get("/traffic/tomtom")
async def get_tomtom_traffic(
    bbox: str = Query(..., description="minLon,minLat,maxLon,maxLat")
):
    """Get traffic flow from TomTom Traffic API."""
    client = TomTomTrafficClient()
    try:
        data = await client.get_traffic_flow(bbox)
        return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TomTom error: {e}")
    finally:
        await client.close()
