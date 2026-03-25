"""
Route recommendation engine.
Scores and ranks running routes based on user preferences and
weather comfort predictions.
"""
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2
from typing import List, Dict, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from loguru import logger

from app.models.routes import RunningRoute, SurfaceType, ElevationProfile
from app.models.weather import WeatherForecast
from app.schemas.routes import RouteRecommendationRequest, WeatherWarning
from app.services.ml.comfort_model import get_comfort_model, engineer_features, compute_comfort_score_heuristic


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


def _get_route_start_coords(route: RunningRoute) -> Optional[Tuple[float, float]]:
    """Extract (lat, lon) from a route's start_point geometry."""
    if route.start_point is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        pt = to_shape(route.start_point)
        return pt.y, pt.x  # lat, lon
    except Exception:
        return None


def compute_match_score(route: RunningRoute, request: RouteRecommendationRequest) -> float:
    """Score how well a route matches the user's stated preferences (0-100)."""
    score = 100.0

    # Distance match
    if request.target_distance_km:
        target = request.target_distance_km
        actual = route.distance_km
        
        # Stricter scoring (Percentage based penalty)
        diff_pct = abs(actual - target) / target
        if diff_pct <= 0.10:
            pass  # perfect match
        elif diff_pct <= 0.25:
            score -= 15
        elif diff_pct <= 0.50:
            score -= 40
        else:
            score -= 80 # Massive penalty for being >50% off

    # Surface match
    if request.preferred_surface != SurfaceType.MIXED:
        if route.surface_type != request.preferred_surface:
            score -= 20

    # Elevation match
    if request.preferred_elevation != ElevationProfile.FLAT:
        if route.elevation_profile != request.preferred_elevation:
            score -= 15
    else:
        if route.elevation_profile == ElevationProfile.HILLY:
            score -= 20

    # Proximity to start point
    start_coords = _get_route_start_coords(route)
    if start_coords:
        dist_km = haversine_km(request.start_lat, request.start_lon, *start_coords)
        if dist_km <= 2:
            pass
        elif dist_km <= 5:
            score -= 5
        elif dist_km <= 10:
            score -= 15
        elif dist_km <= 20:
            score -= 25
        else:
            score -= 40

    return max(0.0, min(100.0, score))


def get_weather_for_window(
    db: Session, zone_id: int, date_str: str, hour_start: int, hour_end: int
) -> List[Dict]:
    """Fetch forecasted weather for a zone during the requested time window."""
    date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    forecasts = db.execute(
        select(WeatherForecast).where(
            and_(
                WeatherForecast.zone_id == zone_id,
                WeatherForecast.forecast_for >= date.replace(hour=hour_start),
                WeatherForecast.forecast_for <= date.replace(hour=hour_end),
            )
        ).order_by(WeatherForecast.forecast_for)
    ).scalars().all()

    result = []
    for f in forecasts:
        result.append({
            "hour": f.forecast_for.hour,
            "datetime": f.forecast_for.isoformat(),
            "temperature": f.temperature,
            "feels_like": f.feels_like,
            "humidity": f.humidity,
            "precipitation": f.precipitation,
            "precipitation_probability": f.precipitation_probability,
            "wind_speed": f.wind_speed,
            "wind_gust": f.wind_gust,
            "cloud_cover": f.cloud_cover,
            "uv_index": f.uv_index,
            "fog": f.fog,
            "weather_description": f.weather_description,
            "comfort_score": f.comfort_score,
        })
    return result


def predict_comfort_for_window(weather_hours: List[Dict], date_str: str) -> float:
    """Compute average comfort score for a time window."""
    if not weather_hours:
        return 0.0  # If no data, don't assume 50 (neutral), assume worst/uncertain

    model = get_comfort_model()
    scores = []
    for w in weather_hours:
        if w.get("comfort_score") is not None:
            scores.append(w["comfort_score"])
        else:
            df = pd.DataFrame([{
                "temperature": w.get("temperature", 14),
                "humidity": w.get("humidity", 75),
                "precipitation": w.get("precipitation", 0),
                "precipitation_probability": w.get("precipitation_probability", 0),
                "wind_speed": w.get("wind_speed", 15),
                "wind_gust": w.get("wind_gust", 20),
                "cloud_cover": w.get("cloud_cover", 50),
                "pressure": 1015,
                "uv_index": w.get("uv_index", 2),
                "solar_radiation": None,
                "fog": w.get("fog", False),
                "hour": w.get("hour", 8),
                "month": int(date_str[5:7]),
                "visibility": None,
            }])
            score = model.predict(df)[0]
            scores.append(float(score))

    return round(sum(scores) / len(scores), 1) if scores else 50.0


def build_weather_warnings(weather_hours: List[Dict]) -> List[WeatherWarning]:
    """Generate human-readable warnings from forecast data."""
    warnings = []
    if not weather_hours:
        return warnings

    max_precip = max((w.get("precipitation") or 0 for w in weather_hours), default=0)
    max_precip_prob = max((w.get("precipitation_probability") or 0 for w in weather_hours), default=0)
    max_wind = max((w.get("wind_speed") or 0 for w in weather_hours), default=0)
    max_gust = max((w.get("wind_gust") or 0 for w in weather_hours), default=0)
    max_temp = max((w.get("temperature") or 0 for w in weather_hours), default=0)
    min_temp = min((w.get("temperature") or 99 for w in weather_hours if w.get("temperature") is not None), default=99)
    max_uv = max((w.get("uv_index") or 0 for w in weather_hours), default=0)
    has_fog = any(w.get("fog") for w in weather_hours)

    if max_precip > 5:
        warnings.append(WeatherWarning(type="rain", message="Lluvia intensa esperada", severity="high"))
    elif max_precip > 1 or max_precip_prob > 60:
        warnings.append(WeatherWarning(type="rain", message="Posibilidad de lluvia", severity="medium"))

    if max_gust > 60 or max_wind > 45:
        warnings.append(WeatherWarning(type="wind", message="Viento muy fuerte — rachas peligrosas", severity="high"))
    elif max_gust > 40 or max_wind > 30:
        warnings.append(WeatherWarning(type="wind", message="Viento fuerte", severity="medium"))

    if has_fog:
        warnings.append(WeatherWarning(type="fog", message="Niebla — visibilidad reducida", severity="medium"))

    if max_temp > 30:
        warnings.append(WeatherWarning(type="heat", message=f"Calor extremo ({max_temp:.0f}°C) — hidratación esencial", severity="high"))
    elif max_temp > 25:
        warnings.append(WeatherWarning(type="heat", message=f"Temperatura alta ({max_temp:.0f}°C)", severity="low"))

    if min_temp < 2:
        warnings.append(WeatherWarning(type="cold", message=f"Temperatura muy baja ({min_temp:.0f}°C) — riesgo de hielo", severity="high"))
    elif min_temp < 5:
        warnings.append(WeatherWarning(type="cold", message=f"Frío ({min_temp:.0f}°C) — abrigate bien", severity="low"))

    if max_uv >= 7:
        warnings.append(WeatherWarning(type="uv", message=f"Índice UV muy alto ({max_uv:.0f}) — protección solar necesaria", severity="medium"))

    return warnings


def summarise_weather(weather_hours: List[Dict]) -> Dict:
    """Build a concise weather summary dict."""
    if not weather_hours:
        return {}
    temps = [w.get("temperature") for w in weather_hours if w.get("temperature") is not None]
    return {
        "temp_min": round(min(temps), 1) if temps else None,
        "temp_max": round(max(temps), 1) if temps else None,
        "temp_avg": round(sum(temps) / len(temps), 1) if temps else None,
        "precipitation_total": round(sum(w.get("precipitation") or 0 for w in weather_hours), 1),
        "max_wind_speed": round(max((w.get("wind_speed") or 0) for w in weather_hours), 1),
        "max_wind_gust": round(max((w.get("wind_gust") or 0) for w in weather_hours), 1),
        "avg_humidity": round(sum(w.get("humidity") or 0 for w in weather_hours) / len(weather_hours), 1),
        "has_fog": any(w.get("fog") for w in weather_hours),
        "max_uv": max((w.get("uv_index") or 0) for w in weather_hours),
    }


def route_to_geojson(route: RunningRoute) -> Optional[Dict]:
    """Convert route geometry to GeoJSON."""
    if route.geom is None:
        return None
    try:
        from geoalchemy2.shape import to_shape
        shape = to_shape(route.geom)
        coords = list(shape.coords)
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for lon, lat in coords],
            },
            "properties": {
                "id": route.id,
                "name": route.name,
                "distance_km": route.distance_km,
            },
        }
    except Exception as e:
        logger.debug(f"GeoJSON conversion failed for route {route.id}: {e}")
        return None


class RecommendationEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_candidate_routes(self, request: RouteRecommendationRequest) -> List[RunningRoute]:
        """Query candidate routes within the search radius."""
        from sqlalchemy import cast
        from geoalchemy2 import Geography
        from geoalchemy2.functions import ST_Distance, ST_MakePoint

        start_point = f"SRID=4326;POINT({request.start_lon} {request.start_lat})"
        radius_m = request.search_radius_km * 1000

        # Base query: filter by proximity to start point
        query = select(RunningRoute).where(
            and_(
                func.ST_DWithin(
                    cast(RunningRoute.start_point, Geography),
                    func.ST_GeogFromText(start_point),
                    radius_m,
                ),
                RunningRoute.distance_km >= 0.5 # NOISE REDUCTION: Ignore segments < 500m
            )
        )

        # 1. Proximity to end point (if provided)
        if request.end_lat is not None and request.end_lon is not None:
             end_point = f"SRID=4326;POINT({request.end_lon} {request.end_lat})"
             query = query.where(
                 func.ST_DWithin(
                     cast(RunningRoute.end_point, Geography),
                     func.ST_GeogFromText(end_point),
                     radius_m,
                 )
             )

        # 2. Surface filter
        if request.preferred_surface != SurfaceType.MIXED:
            # If user specified a surface, be strict
            query = query.where(RunningRoute.surface_type == request.preferred_surface)

        # 3. Distance filter (Harder range ±25% if focused, otherwise ±50%)
        if request.target_distance_km:
            lo = request.target_distance_km * 0.75
            hi = request.target_distance_km * 1.25
            query = query.where(RunningRoute.distance_km.between(lo, hi))

        # 4. Elevation filter
        if request.preferred_elevation == ElevationProfile.FLAT:
            query = query.where(RunningRoute.elevation_profile == ElevationProfile.FLAT)
        elif request.preferred_elevation == ElevationProfile.MODERATE:
            query = query.where(RunningRoute.elevation_profile == ElevationProfile.MODERATE)
        elif request.preferred_elevation == ElevationProfile.HILLY:
            query = query.where(RunningRoute.elevation_profile == ElevationProfile.HILLY)

        query = query.limit(50)
        candidates = self.db.execute(query).scalars().all()

        return candidates


    def recommend(self, request: RouteRecommendationRequest) -> List[Dict]:
        """Return top N route recommendations with comfort scores."""
        candidates = self.get_candidate_routes(request)
        logger.info(f"Found {len(candidates)} candidate routes")

        if not candidates:
            return []

        scored = []
        # Handle optional date and time
        target_date = request.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ts = request.time_start if request.time_start is not None else 7
        te = request.time_end if request.time_end is not None else 23

        for route in candidates:
            zone_id = route.zone_id or 1
            weather_hours = get_weather_for_window(
                self.db, zone_id, target_date, ts, te
            )
            comfort_score = predict_comfort_for_window(weather_hours, target_date)
            match_score = compute_match_score(route, request)
            overall = comfort_score * 0.55 + match_score * 0.45
            warnings = build_weather_warnings(weather_hours)
            weather_summary = summarise_weather(weather_hours)
            geojson = route_to_geojson(route)

            scored.append({
                "route": route,
                "comfort_score": comfort_score,
                "match_score": match_score,
                "overall_score": round(overall, 1),
                "weather_hours": weather_hours,
                "warnings": warnings,
                "weather_summary": weather_summary,
                "geojson": geojson,
            })

        # Sort by overall score descending
        scored.sort(key=lambda x: x["overall_score"], reverse=True)

        # Assign ranks
        for i, item in enumerate(scored[:request.max_results]):
            item["rank"] = i + 1

        return scored[:request.max_results]
