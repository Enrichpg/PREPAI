"""Unit tests for weather data parsers."""
import pytest
from datetime import datetime, timezone
from app.services.weather.aemet_client import parse_aemet_observation
class TestAEMETParser:
    def test_parse_valid_observation(self):
        raw = {
            "fint": "2023-06-15T08:00:00UTC",
            "ta": "18.5",
            "hr": "72",
            "prec": "0.0",
            "vv": "12.3",
            "vmax": "18.0",
            "dv": "NO",  # AEMET uses Spanish cardinal: NO = Noroeste = 315°
            "pres": "1013.5",
            "vis": "15.0",
        }
        result = parse_aemet_observation(raw, "1387")
        assert result is not None
        assert result["temperature"] == pytest.approx(18.5)
        assert result["humidity"] == pytest.approx(72.0)
        assert result["precipitation"] == pytest.approx(0.0)
        assert result["wind_speed"] == pytest.approx(12.3)
        assert result["wind_gust"] == pytest.approx(18.0)
        assert result["wind_direction"] == pytest.approx(315.0)  # NW = 315
        assert result["pressure"] == pytest.approx(1013.5)

    def test_parse_cardinal_wind_directions(self):
        # AEMET uses Spanish cardinal directions
        dirs = {
            "N": 0, "NE": 45, "E": 90, "SE": 135,
            "S": 180, "SO": 225, "O": 270, "NO": 315,
        }
        for cardinal, expected in dirs.items():
            raw = {"fint": "2023-01-01T00:00:00UTC", "dv": cardinal}
            result = parse_aemet_observation(raw, "1387")
            assert result is not None
            assert result["wind_direction"] == pytest.approx(expected)

    def test_parse_missing_fields_returns_none_values(self):
        raw = {"fint": "2023-06-15T10:00:00UTC"}
        result = parse_aemet_observation(raw, "1387")
        assert result is not None
        assert result["temperature"] is None
        assert result["humidity"] is None

    def test_parse_invalid_timestamp_returns_none(self):
        raw = {"fint": "not-a-date"}
        result = parse_aemet_observation(raw, "1387")
        assert result is None

    def test_parse_missing_timestamp_returns_none(self):
        raw = {"ta": "15.0"}
        result = parse_aemet_observation(raw, "1387")
        assert result is None

    def test_parse_comma_decimal_values(self):
        raw = {"fint": "2023-01-01T00:00:00UTC", "ta": "12,5", "hr": "80,0"}
        result = parse_aemet_observation(raw, "1387")
        assert result is not None
        assert result["temperature"] == pytest.approx(12.5)
        assert result["humidity"] == pytest.approx(80.0)


