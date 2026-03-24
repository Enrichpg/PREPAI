"""
Process raw API forecast data into WeatherForecast DB records.
"""
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from loguru import logger

from app.models.weather import WeatherForecast, DataSource
from app.models.zones import Zone


async def _get_zone_by_municipality(db: Session, municipality: str) -> int:
    """Find zone_id by municipality name (best effort)."""
    zone = db.execute(
        select(Zone).where(Zone.municipality.ilike(f"%{municipality}%"))
    ).scalar_one_or_none()
    if zone:
        return zone.id
    # Return zone_id=1 as fallback (main A Coruña city zone)
    return 1


async def _upsert_forecast(db: Session, zone_id: int, forecast_for: datetime,
                           generated_at: datetime, source: DataSource, data: Dict) -> bool:
    existing = db.execute(
        select(WeatherForecast).where(
            and_(
                WeatherForecast.zone_id == zone_id,
                WeatherForecast.forecast_for == forecast_for,
                WeatherForecast.source == source,
            )
        )
    ).scalar_one_or_none()

    fields = {
        "temperature": data.get("temperature"),
        "feels_like": data.get("feels_like"),
        "humidity": data.get("humidity"),
        "precipitation": data.get("precipitation"),
        "precipitation_probability": data.get("precipitation_probability"),
        "wind_speed": data.get("wind_speed"),
        "wind_gust": data.get("wind_gust"),
        "wind_direction": data.get("wind_direction"),
        "pressure": data.get("pressure"),
        "cloud_cover": data.get("cloud_cover"),
        "uv_index": data.get("uv_index"),
        "fog": data.get("fog", False),
        "weather_code": data.get("weather_code"),
        "weather_description": data.get("weather_description"),
    }

    if existing:
        for k, v in fields.items():
            if v is not None:
                setattr(existing, k, v)
        db.commit()
        return False

    record = WeatherForecast(
        zone_id=zone_id,
        forecast_for=forecast_for,
        generated_at=generated_at,
        source=source,
        **fields,
    )
    db.add(record)
    db.commit()
    return True


async def process_aemet_forecasts(db: Session, raw_forecasts: List[Dict]) -> int:
    """Process AEMET municipal forecasts into DB."""
    inserted = 0
    generated_at = datetime.now(timezone.utc)

    for item in raw_forecasts:
        try:
            prediccion = item.get("prediccion") or {}
            dias = prediccion.get("dia") or []
            if isinstance(dias, dict):
                dias = [dias]

            nombre = item.get("nombre", "")
            zone_id = await _get_zone_by_municipality(db, nombre)

            for dia in dias:
                fecha_str = dia.get("fecha", "")
                hora_data = dia.get("hora") or dia.get("viento") or []

                if isinstance(hora_data, list):
                    for h in hora_data:
                        hora = int(h.get("periodo", 0))
                        if not (0 <= hora <= 23):
                            continue
                        try:
                            forecast_for = datetime.fromisoformat(f"{fecha_str}T{hora:02d}:00:00+00:00")
                        except ValueError:
                            continue

                        data = {
                            "temperature": _safe_float(h.get("value") or h.get("temperatura")),
                            "precipitation": _safe_float(dia.get("probPrecipitacion", {}).get("value") if isinstance(dia.get("probPrecipitacion"), dict) else None),
                            "wind_speed": _safe_float(h.get("velocidad")),
                            "wind_direction": _parse_wind_dir(h.get("direccion")),
                            "humidity": _safe_float(dia.get("humedadRelativa", {}).get("value") if isinstance(dia.get("humedadRelativa"), dict) else None),
                        }
                        ok = await _upsert_forecast(db, zone_id, forecast_for, generated_at, DataSource.AEMET, data)
                        if ok:
                            inserted += 1
        except Exception as e:
            logger.debug(f"AEMET forecast processing error: {e}")

    return inserted




def _safe_float(val) -> float:
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _parse_wind_dir(val) -> float:
    wind_dir_map = {
        "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
        "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
        "S": 180, "SSO": 202.5, "SO": 225, "OSO": 247.5,
        "O": 270, "ONO": 292.5, "NO": 315, "NNO": 337.5,
    }
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    return wind_dir_map.get(str(val).upper())
