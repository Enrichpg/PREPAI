"""Unit tests for the route recommendation scoring logic."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.routes.recommendation import (
    compute_match_score,
    build_weather_warnings,
    summarise_weather,
    predict_comfort_for_window,
)
from app.models.routes import RunningRoute, SurfaceType, ElevationProfile
from app.schemas.routes import RouteRecommendationRequest


def _make_request(**kwargs):
    defaults = {
        "preferred_surface": SurfaceType.MIXED,
        "preferred_elevation": ElevationProfile.FLAT,
        "start_lat": 43.3623,
        "start_lon": -8.4115,
        "date": "2024-06-15",
        "time_start": 7,
        "time_end": 9,
        "max_results": 5,
        "search_radius_km": 30.0,
    }
    defaults.update(kwargs)
    return RouteRecommendationRequest(**defaults)


def _make_route(**kwargs):
    route = MagicMock(spec=RunningRoute)
    route.id = 1
    route.distance_km = 10.0
    route.surface_type = SurfaceType.MIXED
    route.elevation_profile = ElevationProfile.FLAT
    route.start_point = None
    for k, v in kwargs.items():
        setattr(route, k, v)
    return route


class TestMatchScore:
    def test_perfect_match_scores_high(self):
        req = _make_request(target_distance_km=10.0)
        route = _make_route(distance_km=10.0)
        score = compute_match_score(route, req)
        assert score >= 90

    def test_distance_mismatch_penalises(self):
        req = _make_request(target_distance_km=10.0)
        close = _make_route(distance_km=10.5)
        far = _make_route(distance_km=25.0)
        assert compute_match_score(close, req) > compute_match_score(far, req)

    def test_surface_mismatch_penalises(self):
        req = _make_request(preferred_surface=SurfaceType.ASPHALT)
        asphalt_route = _make_route(surface_type=SurfaceType.ASPHALT)
        trail_route = _make_route(surface_type=SurfaceType.TRAIL)
        assert compute_match_score(asphalt_route, req) > compute_match_score(trail_route, req)

    def test_elevation_mismatch_penalises_flat_preference(self):
        req = _make_request(preferred_elevation=ElevationProfile.FLAT)
        flat = _make_route(elevation_profile=ElevationProfile.FLAT)
        hilly = _make_route(elevation_profile=ElevationProfile.HILLY)
        assert compute_match_score(flat, req) > compute_match_score(hilly, req)

    def test_score_bounded(self):
        req = _make_request(target_distance_km=10)
        for dist in [1, 5, 10, 20, 100]:
            route = _make_route(distance_km=dist)
            score = compute_match_score(route, req)
            assert 0 <= score <= 100


class TestWeatherWarnings:
    def test_heavy_rain_warning(self):
        hours = [{"precipitation": 20, "wind_speed": 5, "wind_gust": 10, "fog": False,
                  "temperature": 15, "uv_index": 2, "precipitation_probability": 90}]
        warnings = build_weather_warnings(hours)
        types = [w.type for w in warnings]
        assert "rain" in types
        rain_w = next(w for w in warnings if w.type == "rain")
        assert rain_w.severity == "high"

    def test_strong_wind_warning(self):
        hours = [{"precipitation": 0, "wind_speed": 70, "wind_gust": 90, "fog": False,
                  "temperature": 15, "uv_index": 2, "precipitation_probability": 0}]
        warnings = build_weather_warnings(hours)
        types = [w.type for w in warnings]
        assert "wind" in types

    def test_fog_warning(self):
        hours = [{"precipitation": 0, "wind_speed": 5, "wind_gust": 8, "fog": True,
                  "temperature": 12, "uv_index": 1, "precipitation_probability": 10}]
        warnings = build_weather_warnings(hours)
        types = [w.type for w in warnings]
        assert "fog" in types

    def test_extreme_heat_warning(self):
        hours = [{"precipitation": 0, "wind_speed": 5, "wind_gust": 8, "fog": False,
                  "temperature": 37, "uv_index": 10, "precipitation_probability": 0}]
        warnings = build_weather_warnings(hours)
        types = [w.type for w in warnings]
        assert "heat" in types
        assert "uv" in types

    def test_ideal_conditions_no_warnings(self):
        hours = [{"precipitation": 0, "wind_speed": 10, "wind_gust": 15, "fog": False,
                  "temperature": 13, "uv_index": 3, "precipitation_probability": 5}]
        warnings = build_weather_warnings(hours)
        assert len(warnings) == 0

    def test_empty_hours_returns_empty(self):
        assert build_weather_warnings([]) == []


class TestWeatherSummary:
    def test_summary_computed_correctly(self):
        hours = [
            {"temperature": 12, "precipitation": 0, "wind_speed": 10, "wind_gust": 15,
             "humidity": 70, "fog": False, "uv_index": 2},
            {"temperature": 15, "precipitation": 1.5, "wind_speed": 12, "wind_gust": 18,
             "humidity": 75, "fog": False, "uv_index": 3},
        ]
        summary = summarise_weather(hours)
        assert summary["temp_min"] == pytest.approx(12.0)
        assert summary["temp_max"] == pytest.approx(15.0)
        assert summary["temp_avg"] == pytest.approx(13.5)
        assert summary["precipitation_total"] == pytest.approx(1.5)
        assert summary["max_wind_speed"] == pytest.approx(12.0)
        assert summary["has_fog"] is False

    def test_fog_detected(self):
        hours = [{"temperature": 10, "precipitation": 0, "wind_speed": 5, "wind_gust": 8,
                  "humidity": 95, "fog": True, "uv_index": 1}]
        summary = summarise_weather(hours)
        assert summary["has_fog"] is True
