from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.routes import SurfaceType, ElevationProfile


class RouteBase(BaseModel):
    name: str
    description: Optional[str] = None
    distance_km: float
    elevation_gain: Optional[float] = None
    elevation_loss: Optional[float] = None
    elevation_min: Optional[float] = None
    elevation_max: Optional[float] = None
    estimated_duration_min: Optional[int] = None
    surface_type: SurfaceType = SurfaceType.MIXED
    elevation_profile: ElevationProfile = ElevationProfile.FLAT
    difficulty: Optional[str] = None
    is_loop: bool = False
    municipality: Optional[str] = None


class RouteOut(RouteBase):
    id: int
    osm_id: Optional[str] = None
    zone_id: Optional[int] = None
    is_verified: bool = False
    elevation_data: Optional[List[Dict[str, float]]] = None
    tags: Optional[Dict[str, Any]] = None
    geojson: Optional[Dict[str, Any]] = None  # GeoJSON LineString

    class Config:
        from_attributes = True


class ElevationPoint(BaseModel):
    distance: float  # km from start
    altitude: float  # metres


class RouteRecommendationRequest(BaseModel):
    target_distance_km: Optional[float] = Field(None, ge=1, le=100)
    target_duration_min: Optional[int] = Field(None, ge=10, le=600)
    preferred_surface: SurfaceType = SurfaceType.MIXED
    preferred_elevation: ElevationProfile = ElevationProfile.FLAT
    start_lat: float = Field(..., ge=42.0, le=44.0)
    start_lon: float = Field(..., ge=-9.5, le=-7.5)
    date: str  # YYYY-MM-DD
    time_start: int = Field(7, ge=0, le=23)
    time_end: int = Field(9, ge=0, le=23)
    max_results: int = Field(5, ge=1, le=10)
    search_radius_km: float = Field(30.0, ge=1, le=100)


class WeatherWarning(BaseModel):
    type: str
    message: str
    severity: str  # low, medium, high


class RouteRecommendationOut(BaseModel):
    route: RouteOut
    comfort_score: float
    match_score: float
    overall_score: float
    rank: int
    weather_summary: Dict[str, Any]
    warnings: List[WeatherWarning]
    hourly_comfort: List[Dict[str, Any]]


class SaveRouteRequest(BaseModel):
    route_id: int
    session_id: str
    nickname: Optional[str] = None
    notes: Optional[str] = None


class SavedRouteOut(BaseModel):
    id: int
    route_id: int
    session_id: str
    nickname: Optional[str] = None
    notes: Optional[str] = None
    share_token: str
    created_at: datetime
    route: Optional[RouteOut] = None

    class Config:
        from_attributes = True
