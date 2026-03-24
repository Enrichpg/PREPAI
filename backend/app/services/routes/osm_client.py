"""
OpenStreetMap Overpass API client for fetching running routes in A Coruña.
"""
import asyncio
from typing import List, Dict, Optional, Tuple
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings


# A Coruña province bounding box [S, W, N, E]
ACORUNA_BBOX = (42.75, -9.30, 43.80, -7.85)


class OverpassClient:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={"Accept": "application/json"},
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=30),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def query(self, ql: str) -> Optional[Dict]:
        resp = await self._client.post(
            settings.OVERPASS_API_URL,
            data={"data": ql},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_running_routes(self) -> List[Dict]:
        """Fetch all running/jogging/trail paths in A Coruña province."""
        s, w, n, e = ACORUNA_BBOX
        bbox = f"{s},{w},{n},{e}"

        query = f"""
        [out:json][timeout:120];
        (
          way["highway"~"path|footway|track|cycleway|pedestrian"]["sport"="running"]({bbox});
          way["route"="running"]({bbox});
          relation["route"="running"]({bbox});
          way["highway"="path"]["surface"~"unpaved|gravel|ground|dirt|grass|sand|compacted"]({bbox});
          way["highway"~"path|footway"]["sac_scale"~"hiking|mountain_hiking"]({bbox});
          way["leisure"="track"]["sport"="athletics"]({bbox});
        );
        out body geom;
        >;
        out skel qt;
        """
        data = await self.query(query)
        return (data or {}).get("elements", [])

    async def get_roads_for_running(self, bbox: Tuple = None) -> List[Dict]:
        """Fetch suitable road segments for road running."""
        s, w, n, e = bbox or ACORUNA_BBOX
        bbox_str = f"{s},{w},{n},{e}"
        query = f"""
        [out:json][timeout:90];
        (
          way["highway"~"residential|tertiary|secondary|unclassified|living_street"]["foot"!="no"]({bbox_str});
          way["highway"~"path|footway"]["foot"!="no"]({bbox_str});
        );
        out body geom;
        """
        data = await self.query(query)
        return (data or {}).get("elements", [])

    async def get_routes_near(self, lat: float, lon: float, radius_m: int = 10000) -> List[Dict]:
        """Fetch routes within radius_m metres of a point."""
        query = f"""
        [out:json][timeout:60];
        (
          way["highway"~"path|footway|track"]
            (around:{radius_m},{lat},{lon});
          way["sport"="running"]
            (around:{radius_m},{lat},{lon});
        );
        out body geom;
        """
        data = await self.query(query)
        return (data or {}).get("elements", [])


def parse_osm_element(element: Dict) -> Optional[Dict]:
    """Convert an OSM element to a route dict with geometry."""
    elem_type = element.get("type")
    if elem_type not in ("way", "relation"):
        return None

    tags = element.get("tags", {})
    geometry = element.get("geometry") or []
    if not geometry and elem_type == "way":
        return None

    # Build coordinate list [[lon, lat], ...]
    coords = [[node["lon"], node["lat"]] for node in geometry if "lat" in node and "lon" in node]
    if len(coords) < 2:
        return None

    # Estimate distance using Haversine
    from math import radians, sin, cos, sqrt, atan2
    total_dist = 0.0
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i-1]
        lon2, lat2 = coords[i]
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        total_dist += R * 2 * atan2(sqrt(a), sqrt(1 - a))

    # Surface detection
    highway = tags.get("highway", "path")
    surface_raw = tags.get("surface", "")
    trail_surfaces = {"unpaved", "gravel", "ground", "dirt", "grass", "sand", "compacted", "fine_gravel"}
    asphalt_surfaces = {"asphalt", "concrete", "paving_stones", "sett", "cobblestone"}

    if surface_raw in trail_surfaces or highway in ("track", "path"):
        surface = "trail"
    elif surface_raw in asphalt_surfaces or highway in ("residential", "tertiary", "secondary", "living_street"):
        surface = "asphalt"
    else:
        surface = "mixed"

    name = tags.get("name") or tags.get("description") or f"Ruta OSM {element.get('id', '')}"

    return {
        "osm_id": str(element.get("id", "")),
        "name": name,
        "coords": coords,
        "distance_km": round(total_dist, 3),
        "surface": surface,
        "tags": tags,
        "start_lat": coords[0][1],
        "start_lon": coords[0][0],
        "end_lat": coords[-1][1],
        "end_lon": coords[-1][0],
    }
