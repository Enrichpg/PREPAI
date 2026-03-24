"""
Event model for storing external events (Eventbrite, etc.)
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    venue = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
