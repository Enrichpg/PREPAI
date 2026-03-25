from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import enum
from app.db.database import Base


class DataSource(str, enum.Enum):
    AEMET = "aemet"
    MANUAL = "manual"


class WeatherStation(Base):
    __tablename__ = "weather_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    municipality = Column(String(200))
    province = Column(String(100), default="A Coruña", index=True)
    source = Column(SAEnum(DataSource), default=DataSource.AEMET, index=True)
    geom = Column(Geometry("POINT", srid=4326), spatial_index=True)
    altitude = Column(Float)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    zone = relationship("Zone", back_populates="weather_stations")
    observations = relationship("WeatherObservation", back_populates="station", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WeatherStation {self.station_id} - {self.name}>"


class WeatherObservation(Base):
    """Historical weather observations stored per station per hour."""
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("weather_stations.id"), nullable=False, index=True)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    source = Column(SAEnum(DataSource), nullable=False)

    # Core meteorological variables
    temperature = Column(Float)           # Celsius
    temperature_min = Column(Float)
    temperature_max = Column(Float)
    feels_like = Column(Float)
    humidity = Column(Float)              # %
    precipitation = Column(Float)         # mm
    precipitation_probability = Column(Float)  # %
    wind_speed = Column(Float)            # km/h
    wind_gust = Column(Float)             # km/h
    wind_direction = Column(Float)        # degrees
    pressure = Column(Float)              # hPa
    visibility = Column(Float)            # km
    cloud_cover = Column(Float)           # %
    uv_index = Column(Float)
    solar_radiation = Column(Float)       # W/m2
    snow_depth = Column(Float)            # cm
    fog = Column(Boolean, default=False)
    weather_code = Column(String(20))
    weather_description = Column(String(200))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    station = relationship("WeatherStation", back_populates="observations")

    def __repr__(self):
        return f"<WeatherObservation station={self.station_id} at={self.observed_at}>"


class WeatherForecast(Base):
    """Weather forecast data per zone per hour."""
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False, index=True)
    forecast_for = Column(DateTime(timezone=True), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(SAEnum(DataSource), nullable=False)

    temperature = Column(Float)
    temperature_min = Column(Float)
    temperature_max = Column(Float)
    feels_like = Column(Float)
    humidity = Column(Float)
    precipitation = Column(Float)
    precipitation_probability = Column(Float)
    wind_speed = Column(Float)
    wind_gust = Column(Float)
    wind_direction = Column(Float)
    pressure = Column(Float)
    visibility = Column(Float)
    cloud_cover = Column(Float)
    uv_index = Column(Float)
    solar_radiation = Column(Float)
    fog = Column(Boolean, default=False)
    weather_code = Column(String(20))
    weather_description = Column(String(200))

    # Comfort score predicted by ML model
    comfort_score = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<WeatherForecast zone={self.zone_id} for={self.forecast_for}>"


class DataIngestionLog(Base):
    """Audit log for all data ingestion runs."""
    __tablename__ = "data_ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(SAEnum(DataSource), nullable=False)
    task_name = Column(String(200))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="running")  # running, success, failed
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    date_range_start = Column(DateTime(timezone=True))
    date_range_end = Column(DateTime(timezone=True))
    error_message = Column(Text)
    ingestion_metadata = Column(JSON)

    def __repr__(self):
        return f"<DataIngestionLog {self.source} {self.status} at={self.started_at}>"
