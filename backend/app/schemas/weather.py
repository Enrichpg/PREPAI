from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.weather import DataSource


class WeatherStationBase(BaseModel):
    station_id: str
    name: str
    municipality: Optional[str] = None
    province: str = "A Coruña"
    source: DataSource = DataSource.AEMET
    altitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WeatherStationCreate(WeatherStationBase):
    pass


class WeatherStationOut(WeatherStationBase):
    id: int
    is_active: bool
    zone_id: Optional[int] = None

    class Config:
        from_attributes = True


class WeatherObservationOut(BaseModel):
    id: int
    station_id: int
    observed_at: datetime
    source: DataSource
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_gust: Optional[float] = None
    wind_direction: Optional[float] = None
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    cloud_cover: Optional[float] = None
    uv_index: Optional[float] = None
    fog: bool = False
    weather_description: Optional[str] = None

    class Config:
        from_attributes = True


class WeatherForecastOut(BaseModel):
    id: int
    zone_id: int
    forecast_for: datetime
    generated_at: datetime
    source: DataSource
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    precipitation_probability: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_gust: Optional[float] = None
    wind_direction: Optional[float] = None
    cloud_cover: Optional[float] = None
    uv_index: Optional[float] = None
    fog: bool = False
    weather_description: Optional[str] = None
    comfort_score: Optional[float] = None

    class Config:
        from_attributes = True


class HourlyComfortForecast(BaseModel):
    hour: int
    datetime: datetime
    comfort_score: float
    temperature: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    weather_description: Optional[str] = None
    warnings: List[str] = []


class ZoneForecastSummary(BaseModel):
    zone_id: int
    zone_name: str
    date: str
    hourly: List[HourlyComfortForecast]
    best_window_start: Optional[int] = None
    best_window_end: Optional[int] = None
    daily_max_comfort: float = 0.0


class DataIngestionLogOut(BaseModel):
    id: int
    source: DataSource
    task_name: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    records_fetched: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class HistoricalStatsOut(BaseModel):
    zone_id: int
    zone_name: str
    month: int
    avg_temperature: Optional[float] = None
    avg_precipitation: Optional[float] = None
    avg_humidity: Optional[float] = None
    avg_wind_speed: Optional[float] = None
    fog_days_pct: Optional[float] = None
    avg_comfort_score: Optional[float] = None
    best_hours: List[int] = []
