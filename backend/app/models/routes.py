from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum as SAEnum, JSON, ARRAY
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import enum
from app.db.database import Base


class SurfaceType(str, enum.Enum):
    ASPHALT = "asphalt"
    TRAIL = "trail"
    MIXED = "mixed"
    GRAVEL = "gravel"
    TRACK = "track"


class ElevationProfile(str, enum.Enum):
    FLAT = "flat"
    MODERATE = "moderate"
    HILLY = "hilly"


class RunningRoute(Base):
    __tablename__ = "running_routes"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(String(100), unique=True, nullable=True, index=True)
    name = Column(String(300), nullable=False, index=True)
    description = Column(Text)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)

    # Geometry: full route as LineString
    geom = Column(Geometry("LINESTRING", srid=4326))
    start_point = Column(Geometry("POINT", srid=4326))
    end_point = Column(Geometry("POINT", srid=4326))

    # Route metrics
    distance_km = Column(Float, nullable=False)
    elevation_gain = Column(Float)       # metres
    elevation_loss = Column(Float)
    elevation_min = Column(Float)
    elevation_max = Column(Float)
    estimated_duration_min = Column(Integer)  # minutes at easy pace

    # Classification
    surface_type = Column(SAEnum(SurfaceType), default=SurfaceType.MIXED)
    elevation_profile = Column(SAEnum(ElevationProfile), default=ElevationProfile.FLAT)
    difficulty = Column(String(20))      # easy, medium, hard
    is_loop = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # Elevation profile as JSON array of {distance, altitude} points
    elevation_data = Column(JSON)

    # Tags
    tags = Column(JSON)

    municipality = Column(String(200))
    source = Column(String(50), default="osm")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    zone = relationship("Zone", back_populates="routes")
    segments = relationship("RouteSegment", back_populates="route", cascade="all, delete-orphan")
    recommendations = relationship("RouteRecommendation", back_populates="route")
    saved_by = relationship("SavedRoute", back_populates="route")

    def __repr__(self):
        return f"<RunningRoute {self.name} ({self.distance_km:.1f}km)>"


class RouteSegment(Base):
    """Individual segments of a route for finer weather overlay."""
    __tablename__ = "route_segments"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("running_routes.id"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    geom = Column(Geometry("LINESTRING", srid=4326))
    distance_km = Column(Float)
    elevation_gain = Column(Float)
    surface_type = Column(SAEnum(SurfaceType))

    # Relationship
    route = relationship("RunningRoute", back_populates="segments")
