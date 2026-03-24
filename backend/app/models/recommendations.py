from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RouteRecommendation(Base):
    __tablename__ = "route_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("running_routes.id"), nullable=False)
    session_id = Column(String(100), index=True)  # anonymous session

    # Request params
    target_distance_km = Column(Float)
    target_duration_min = Column(Integer)
    preferred_surface = Column(String(50))
    preferred_elevation = Column(String(50))
    start_lat = Column(Float)
    start_lon = Column(Float)
    requested_date = Column(DateTime(timezone=True))
    requested_time_start = Column(Integer)  # hour 0-23
    requested_time_end = Column(Integer)

    # Scores
    comfort_score = Column(Float)
    match_score = Column(Float)      # how well route matches user criteria
    overall_score = Column(Float)
    rank = Column(Integer)

    # Weather at time of recommendation
    weather_summary = Column(JSON)
    warnings = Column(JSON)          # list of warning strings

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    route = relationship("RunningRoute", back_populates="recommendations")


class SavedRoute(Base):
    __tablename__ = "saved_routes"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("running_routes.id"), nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    nickname = Column(String(200))
    notes = Column(Text)
    share_token = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    route = relationship("RunningRoute", back_populates="saved_by")
