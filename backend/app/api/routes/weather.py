from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from typing import List, Optional
from datetime import datetime, date, timezone
from loguru import logger

from app.db.database import get_db
from app.models.weather import WeatherStation, WeatherObservation, WeatherForecast, DataIngestionLog, DataSource
from app.schemas.weather import (
    WeatherStationOut, WeatherObservationOut, WeatherForecastOut,
    ZoneForecastSummary, HourlyComfortForecast, DataIngestionLogOut, HistoricalStatsOut
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/stations", response_model=List[WeatherStationOut])
async def list_stations(
    source: Optional[DataSource] = None,
    municipality: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all weather stations in A Coruña province."""
    query = select(WeatherStation).where(WeatherStation.is_active == True)
    if source:
        query = query.where(WeatherStation.source == source)
    if municipality:
        query = query.where(WeatherStation.municipality.ilike(f"%{municipality}%"))
    result = await db.execute(query.order_by(WeatherStation.name))
    stations = result.scalars().all()

    out = []
    for s in stations:
        lat = lon = None
        if s.geom:
            try:
                from geoalchemy2.shape import to_shape
                pt = to_shape(s.geom)
                lat, lon = pt.y, pt.x
            except Exception:
                pass
        out.append(WeatherStationOut(
            id=s.id,
            station_id=s.station_id,
            name=s.name,
            municipality=s.municipality,
            province=s.province,
            source=s.source,
            altitude=s.altitude,
            latitude=lat,
            longitude=lon,
            is_active=s.is_active,
            zone_id=s.zone_id,
        ))
    return out


@router.get("/stations/{station_id}/observations", response_model=List[WeatherObservationOut])
async def get_station_observations(
    station_id: int,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = Query(default=168, le=2000),
    db: AsyncSession = Depends(get_db),
):
    """Get observations for a specific station."""
    query = select(WeatherObservation).where(WeatherObservation.station_id == station_id)
    if start:
        query = query.where(WeatherObservation.observed_at >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(WeatherObservation.observed_at <= datetime.combine(end, datetime.max.time()))
    query = query.order_by(WeatherObservation.observed_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/forecasts/{zone_id}", response_model=ZoneForecastSummary)
async def get_zone_forecast(
    zone_id: int,
    target_date: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
):
    """Get hourly comfort forecast for a zone."""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    query = select(WeatherForecast).where(
        and_(
            WeatherForecast.zone_id == zone_id,
            WeatherForecast.forecast_for >= dt,
            WeatherForecast.forecast_for < dt.replace(hour=23, minute=59),
        )
    ).order_by(WeatherForecast.forecast_for)

    result = await db.execute(query)
    forecasts = result.scalars().all()

    hourly = []
    for f in forecasts:
        warnings = []
        if f.precipitation and f.precipitation > 2:
            warnings.append("lluvia")
        if f.fog:
            warnings.append("niebla")
        if f.wind_speed and f.wind_speed > 40:
            warnings.append("viento fuerte")
        if f.temperature and f.temperature > 28:
            warnings.append("calor")

        hourly.append(HourlyComfortForecast(
            hour=f.forecast_for.hour,
            datetime=f.forecast_for,
            comfort_score=f.comfort_score or 50.0,
            temperature=f.temperature,
            precipitation=f.precipitation,
            wind_speed=f.wind_speed,
            humidity=f.humidity,
            weather_description=f.weather_description,
            warnings=warnings,
        ))

    best_start = best_end = None
    daily_max = 0.0
    if hourly:
        best = max(hourly, key=lambda h: h.comfort_score)
        daily_max = best.comfort_score
        best_start = best.hour
        best_end = min(best.hour + 2, 23)

    # Get zone name
    zone_name = f"Zona {zone_id}"
    try:
        from app.models.zones import Zone
        zone_result = await db.execute(select(Zone).where(Zone.id == zone_id))
        zone = zone_result.scalar_one_or_none()
        if zone:
            zone_name = zone.name
    except Exception:
        pass

    return ZoneForecastSummary(
        zone_id=zone_id,
        zone_name=zone_name,
        date=dt.strftime("%Y-%m-%d"),
        hourly=hourly,
        best_window_start=best_start,
        best_window_end=best_end,
        daily_max_comfort=daily_max,
    )


@router.get("/heatmap", response_model=List[dict])
async def get_comfort_heatmap(
    target_date: Optional[str] = Query(default=None),
    hour: Optional[int] = Query(default=None, ge=0, le=23),
    db: AsyncSession = Depends(get_db),
):
    """Return comfort scores per zone for heatmap rendering."""
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    query = """
        SELECT
            z.id AS zone_id,
            z.name AS zone_name,
            ST_Y(z.centroid::geometry) AS lat,
            ST_X(z.centroid::geometry) AS lon,
            AVG(wf.comfort_score) AS avg_comfort,
            MAX(wf.comfort_score) AS max_comfort
        FROM zones z
        LEFT JOIN weather_forecasts wf ON wf.zone_id = z.id
            AND DATE(wf.forecast_for) = :target_date
            {}
        GROUP BY z.id, z.name, z.centroid
        ORDER BY z.name
    """.format("AND EXTRACT(HOUR FROM wf.forecast_for) = :hour" if hour is not None else "")

    params = {"target_date": dt.date()}
    if hour is not None:
        params["hour"] = hour

    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return [
        {
            "zone_id": r.zone_id,
            "zone_name": r.zone_name,
            "lat": r.lat,
            "lon": r.lon,
            "avg_comfort": round(float(r.avg_comfort), 1) if r.avg_comfort else None,
            "max_comfort": round(float(r.max_comfort), 1) if r.max_comfort else None,
        }
        for r in rows
    ]


@router.get("/historical/stats", response_model=List[HistoricalStatsOut])
async def get_historical_stats(
    zone_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get monthly historical statistics per zone."""
    query = """
        SELECT
            z.id AS zone_id,
            z.name AS zone_name,
            EXTRACT(MONTH FROM wo.observed_at) AS month,
            AVG(wo.temperature) AS avg_temperature,
            AVG(wo.precipitation) AS avg_precipitation,
            AVG(wo.humidity) AS avg_humidity,
            AVG(wo.wind_speed) AS avg_wind_speed,
            100.0 * SUM(CASE WHEN wo.fog THEN 1 ELSE 0 END) / COUNT(*) AS fog_days_pct
        FROM zones z
        JOIN weather_stations ws ON ws.zone_id = z.id
        JOIN weather_observations wo ON wo.station_id = ws.id
        {}
        GROUP BY z.id, z.name, EXTRACT(MONTH FROM wo.observed_at)
        ORDER BY z.id, month
    """.format("WHERE z.id = :zone_id" if zone_id else "")

    params = {"zone_id": zone_id} if zone_id else {}
    result = await db.execute(text(query), params)
    rows = result.fetchall()

    return [
        HistoricalStatsOut(
            zone_id=r.zone_id,
            zone_name=r.zone_name,
            month=int(r.month),
            avg_temperature=round(float(r.avg_temperature), 1) if r.avg_temperature else None,
            avg_precipitation=round(float(r.avg_precipitation), 2) if r.avg_precipitation else None,
            avg_humidity=round(float(r.avg_humidity), 1) if r.avg_humidity else None,
            avg_wind_speed=round(float(r.avg_wind_speed), 1) if r.avg_wind_speed else None,
            fog_days_pct=round(float(r.fog_days_pct), 1) if r.fog_days_pct else None,
        )
        for r in rows
    ]


@router.get("/ingestion/logs", response_model=List[DataIngestionLogOut])
async def get_ingestion_logs(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
):
    """View recent data ingestion audit logs."""
    result = await db.execute(
        select(DataIngestionLog)
        .order_by(DataIngestionLog.started_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/ingestion/trigger")
async def trigger_ingestion(background_tasks: BackgroundTasks):
    """Manually trigger a weather data refresh (last 8 days)."""
    from app.services.weather.tasks import fetch_all_weather_data
    task = fetch_all_weather_data.delay()
    return {"task_id": task.id, "message": "Ingestion task queued"}


@router.post("/ingestion/historical")
async def trigger_historical_ingestion(years: int = Query(default=10, ge=1, le=15)):
    """Manually trigger historical backfill."""
    from app.services.weather.tasks import fetch_historical_weather
    task = fetch_historical_weather.delay(years=years)
    return {"task_id": task.id, "message": f"Historical ingestion for {years} years queued"}
