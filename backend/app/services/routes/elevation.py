"""
Elevation data fetching from open-elevation API (backed by SRTM/NASA).
Fallback: Open-Elevation public instance.
"""
import asyncio
from typing import List, Dict, Optional, Tuple
import httpx
from loguru import logger


OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"


async def get_elevation_for_route(coords: List[List[float]], sample_every: int = 10) -> List[Dict]:
    """
    Given [[lon, lat], ...] coordinates, fetch elevation data.
    Samples every N points to respect API limits.
    Returns list of {distance, altitude} dicts.
    """
    if not coords:
        return []

    # Sample coordinates
    sampled = coords[::sample_every]
    if coords[-1] not in sampled:
        sampled.append(coords[-1])

    locations = [{"latitude": lat, "longitude": lon} for lon, lat in sampled]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                OPEN_ELEVATION_URL,
                json={"locations": locations},
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
    except Exception as e:
        logger.warning(f"Elevation API error: {e} — using flat profile")
        results = [{"elevation": 0} for _ in sampled]

    # Compute cumulative distance for each sample
    from math import radians, sin, cos, sqrt, atan2
    elevation_profile = []
    cumulative_dist = 0.0

    for i, (result, (lon, lat)) in enumerate(zip(results, [(c[0], c[1]) for c in sampled])):
        if i > 0:
            prev_lon, prev_lat = sampled[i-1]
            R = 6371.0
            dlat = radians(lat - prev_lat)
            dlon = radians(lon - prev_lon)
            a = sin(dlat/2)**2 + cos(radians(prev_lat)) * cos(radians(lat)) * sin(dlon/2)**2
            cumulative_dist += R * 2 * atan2(sqrt(a), sqrt(1 - a))

        elevation_profile.append({
            "distance": round(cumulative_dist, 3),
            "altitude": result.get("elevation", 0),
        })

    return elevation_profile


def compute_elevation_stats(elevation_profile: List[Dict]) -> Dict:
    """Compute gain, loss, min, max from elevation profile."""
    if not elevation_profile:
        return {"gain": 0, "loss": 0, "min": 0, "max": 0}

    altitudes = [p["altitude"] for p in elevation_profile]
    gain = loss = 0.0
    for i in range(1, len(altitudes)):
        diff = altitudes[i] - altitudes[i-1]
        if diff > 0:
            gain += diff
        else:
            loss += abs(diff)

    return {
        "gain": round(gain, 1),
        "loss": round(loss, 1),
        "min": round(min(altitudes), 1),
        "max": round(max(altitudes), 1),
    }


def classify_elevation_profile(gain: float, distance_km: float) -> str:
    """Classify route as flat/moderate/hilly based on gain per km."""
    if distance_km <= 0:
        return "flat"
    gain_per_km = gain / distance_km
    if gain_per_km < 20:
        return "flat"
    elif gain_per_km < 50:
        return "moderate"
    else:
        return "hilly"
