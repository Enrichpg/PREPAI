"""
Weather data ingestion pipeline.
Coordinates AEMET data fetching and stores to DB.
"""
import asyncio
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from loguru import logger
from geoalchemy2.elements import WKTElement

from app.db.database import SyncSessionLocal
from app.models.weather import WeatherStation, WeatherObservation, DataIngestionLog, DataSource
from app.models.zones import Zone
from app.services.weather.aemet_client import AEMETClient, parse_aemet_observation, ACORUNA_STATIONS


class WeatherIngestionPipeline:
    def __init__(self):
        self.db: Session = SyncSessionLocal()

    def close(self):
        self.db.close()

    def _log_start(self, source: DataSource, task_name: str, date_start: date, date_end: date) -> DataIngestionLog:
        log = DataIngestionLog(
            source=source,
            task_name=task_name,
            status="running",
            date_range_start=datetime.combine(date_start, datetime.min.time()),
            date_range_end=datetime.combine(date_end, datetime.min.time()),
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def _log_finish(self, log: DataIngestionLog, status: str, fetched: int, inserted: int, updated: int, error: str = None):
        log.finished_at = datetime.utcnow()
        log.status = status
        log.records_fetched = fetched
        log.records_inserted = inserted
        log.records_updated = updated
        log.error_message = error
        self.db.commit()

    def _get_or_create_station(self, station_data: Dict, source: DataSource) -> Optional[WeatherStation]:
        external_id = str(station_data.get("indicativo") or station_data.get("idEstacion") or station_data.get("station_external_id", ""))
        if not external_id:
            return None

        station = self.db.execute(
            select(WeatherStation).where(WeatherStation.station_id == external_id)
        ).scalar_one_or_none()

        if not station:
            lat = station_data.get("latitud") or station_data.get("lat")
            lon = station_data.get("longitud") or station_data.get("lon")
            try:
                lat = float(str(lat).replace(",", ".")) if lat else None
                lon = float(str(lon).replace(",", ".")) if lon else None
            except (ValueError, TypeError):
                lat, lon = None, None

            geom = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat and lon else None
            station = WeatherStation(
                station_id=external_id,
                name=station_data.get("nombre") or station_data.get("estacion") or external_id,
                municipality=station_data.get("municipio") or station_data.get("concello"),
                source=source,
                geom=geom,
                altitude=station_data.get("altitud"),
                is_active=True,
            )
            self.db.add(station)
            self.db.commit()
            self.db.refresh(station)
        return station

    def _upsert_observation(self, station: WeatherStation, obs: Dict, source: DataSource) -> str:
        """Insert or update an observation. Returns 'inserted' or 'updated'."""
        observed_at = obs["observed_at"]
        existing = self.db.execute(
            select(WeatherObservation).where(
                and_(
                    WeatherObservation.station_id == station.id,
                    WeatherObservation.observed_at == observed_at,
                )
            )
        ).scalar_one_or_none()

        if existing:
            for field in [
                "temperature", "temperature_min", "temperature_max",
                "humidity", "precipitation", "wind_speed", "wind_gust",
                "wind_direction", "pressure", "visibility", "cloud_cover",
                "uv_index", "solar_radiation", "fog",
            ]:
                val = obs.get(field)
                if val is not None:
                    setattr(existing, field, val)
            self.db.commit()
            return "updated"
        else:
            record = WeatherObservation(
                station_id=station.id,
                observed_at=observed_at,
                source=source,
                temperature=obs.get("temperature"),
                temperature_min=obs.get("temperature_min"),
                temperature_max=obs.get("temperature_max"),
                humidity=obs.get("humidity"),
                precipitation=obs.get("precipitation"),
                wind_speed=obs.get("wind_speed"),
                wind_gust=obs.get("wind_gust"),
                wind_direction=obs.get("wind_direction"),
                pressure=obs.get("pressure"),
                visibility=obs.get("visibility"),
                cloud_cover=obs.get("cloud_cover"),
                uv_index=obs.get("uv_index"),
                solar_radiation=obs.get("solar_radiation"),
                fog=obs.get("fog", False),
            )
            self.db.add(record)
            self.db.commit()
            return "inserted"

    async def ingest_aemet(self, start: date, end: date) -> Dict:
        log = self._log_start(DataSource.AEMET, "ingest_aemet", start, end)
        total_fetched = total_inserted = total_updated = 0

        try:
            async with AEMETClient() as client:
                # Sync station list
                stations_raw = await client.get_stations()
                logger.info(f"AEMET: found {len(stations_raw)} A Coruña stations")

                for station_raw in stations_raw:
                    try:
                        station = self._get_or_create_station(station_raw, DataSource.AEMET)
                        if not station:
                            continue

                        station_id = station_raw.get("indicativo")
                        obs_raw = await client.get_historical_observations(station_id, start, end)
                        total_fetched += len(obs_raw)

                        for raw in obs_raw:
                            parsed = parse_aemet_observation(raw, station_id)
                            if not parsed:
                                continue
                            result = self._upsert_observation(station, parsed, DataSource.AEMET)
                            if result == "inserted":
                                total_inserted += 1
                            else:
                                total_updated += 1
                    except Exception as e:
                        logger.error(f"AEMET ingestion error for station {station_raw}: {e}")

            self._log_finish(log, "success", total_fetched, total_inserted, total_updated)
        except Exception as e:
            logger.error(f"AEMET ingestion fatal error: {e}")
            self._log_finish(log, "failed", total_fetched, total_inserted, total_updated, str(e))
            raise

        from app.services.ml.tasks import retrain_model
        retrain_model.delay()
        return {"fetched": total_fetched, "inserted": total_inserted, "updated": total_updated}


    async def ingest_all(self, years: int = 10) -> Dict:
        """Run full historical ingestion for the last N years."""
        end = date.today()
        start = date(end.year - years, end.month, end.day)
        logger.info(f"Starting full ingestion from {start} to {end}")

        aemet_result = await self.ingest_aemet(start, end)
        from app.services.ml.tasks import retrain_model
        retrain_model.delay()
        return {
            "aemet": aemet_result,
        }

    async def refresh_forecasts(self) -> Dict:
        """Fetch and store latest forecast data from AEMET only."""
        log = self._log_start(
            DataSource.AEMET, "refresh_forecasts",
            date.today(), date.today() + timedelta(days=7)
        )
        inserted = 0
        try:
            from app.services.weather.forecast_processor import process_aemet_forecasts
            async with AEMETClient() as aemet_client:
                forecasts = await aemet_client.get_forecast_all_acoruna()
                inserted += await process_aemet_forecasts(self.db, forecasts)
            self._log_finish(log, "success", inserted, inserted, 0)
        except Exception as e:
            logger.error(f"Forecast refresh error: {e}")
            self._log_finish(log, "failed", inserted, inserted, 0, str(e))
            raise
        from app.services.ml.tasks import retrain_model
        retrain_model.delay()
        return {"inserted": inserted}
