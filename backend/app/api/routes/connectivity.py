"""
Connectivity check endpoint.
Tests that the 3 active external APIs are reachable.
"""
import asyncio
from typing import Dict
from fastapi import APIRouter
import httpx
from loguru import logger

from app.core.config import settings

router = APIRouter(prefix="/connectivity", tags=["connectivity"])


async def _check_aemet() -> Dict:
    """
    Test AEMET OpenData — hit the station inventory endpoint with api_key auth.
    AEMET responds with {estado:200, datos:'<url>'} on success.
    """
    url = f"{settings.AEMET_BASE_URL}/valores/climatologicos/inventarioestaciones/todasestaciones/"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params={"api_key": settings.AEMET_API_KEY})
            if resp.status_code == 200:
                body = resp.json()
                estado = body.get("estado")
                if estado == 200:
                    return {"status": "ok", "http_code": 200, "aemet_estado": estado}
                return {"status": "error", "http_code": 200, "aemet_estado": estado,
                        "detail": body.get("descripcion", "")}
            return {"status": "error", "http_code": resp.status_code, "detail": resp.text[:200]}
    except Exception as e:
        logger.warning(f"AEMET connectivity check failed: {e}")
        return {"status": "error", "detail": str(e)}


async def _check_osm_overpass() -> Dict:
    """Test OSM Overpass — minimal query to verify the endpoint is up."""
    query = "[out:json][timeout:5];node(43.36,-8.43,43.38,-8.41)[amenity=cafe];out 1;"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(settings.OVERPASS_API_URL, data={"data": query})
            if resp.status_code == 200:
                data = resp.json()
                return {"status": "ok", "http_code": 200, "elements_returned": len(data.get("elements", []))}
            return {"status": "error", "http_code": resp.status_code, "detail": resp.text[:200]}
    except Exception as e:
        logger.warning(f"OSM Overpass connectivity check failed: {e}")
        return {"status": "error", "detail": str(e)}


async def _check_open_elevation() -> Dict:
    """Test Open-Elevation — request elevation for A Coruña city centre."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                settings.OPEN_ELEVATION_URL,
                json={"locations": [{"latitude": 43.3713, "longitude": -8.3960}]},
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                elevation = results[0].get("elevation") if results else None
                return {"status": "ok", "http_code": 200, "elevation_m": elevation}
            return {"status": "error", "http_code": resp.status_code, "detail": resp.text[:200]}
    except Exception as e:
        logger.warning(f"Open-Elevation connectivity check failed: {e}")
        return {"status": "error", "detail": str(e)}


@router.get("")
async def check_connectivity():
    """
    Test connectivity to all 3 active external APIs in parallel.
    Returns status for each: ok | error
    """
    aemet, overpass, elevation = await asyncio.gather(
        _check_aemet(),
        _check_osm_overpass(),
        _check_open_elevation(),
    )

    overall = "ok" if all(r["status"] == "ok" for r in [aemet, overpass, elevation]) else "degraded"

    return {
        "overall": overall,
        "apis": {
            "aemet": aemet,
            "osm_overpass": overpass,
            "open_elevation": elevation,
        },
    }
