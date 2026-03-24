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
            "dv": "NW",
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


class TestMeteoGaliciaParser:
    def test_parse_valid_observation(self):
        raw = {
            "instantedt": "2023-06-15T08:00:00",
            "temperatura": 17.8,
            "humedadeRelativa": 78,
            "precipitacion": 0.2,
            "velocidadeVento": 15.0,
            "rachaMaxVento": 22.0,
            "direccionVento": 270.0,
            "presionAtmosfera": 1012.0,
            "visibilidade": 12.0,
        }
        result = parse_meteogalicia_observation(raw, 10045)
        assert result is not None
        assert result["temperature"] == pytest.approx(17.8)
        assert result["humidity"] == pytest.approx(78.0)
        assert result["precipitation"] == pytest.approx(0.2)
        assert result["wind_speed"] == pytest.approx(15.0)
        assert result["fog"] is False

    def test_fog_detected_low_visibility(self):
        raw = {
            "instantedt": "2023-11-01T07:00:00",
            "temperatura": 10.0,
            "visibilidade": 0.3,
        }
        result = parse_meteogalicia_observation(raw, 10045)
        assert result is not None
        assert result["fog"] is True

    def test_null_sentinel_values_become_none(self):
        raw = {
            "instantedt": "2023-01-01T12:00:00",
            "temperatura": -9999,
            "humedadeRelativa": -9999.0,
        }
        result = parse_meteogalicia_observation(raw, 10045)
        assert result is not None
        assert result["temperature"] is None
        assert result["humidity"] is None

    def test_unix_timestamp_milliseconds(self):
        ts_ms = 1686816000000  # 2023-06-15T12:00:00 UTC in ms
        raw = {"instantedt": ts_ms, "temperatura": 20.0}
        result = parse_meteogalicia_observation(raw, 10045)
        assert result is not None
        assert result["observed_at"].year == 2023
