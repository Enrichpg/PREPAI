"""
Traffic model for storing traffic data from TomTom and other APIs.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TrafficData(Base):
    __tablename__ = "traffic_data"
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer)
    timestamp = Column(DateTime, nullable=False)
    traffic_level = Column(Float, nullable=False)  # e.g., congestion index
    description = Column(String)
