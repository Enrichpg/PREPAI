from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    municipality = Column(String(200), nullable=False, index=True)
    comarca = Column(String(200))
    province = Column(String(100), default="A Coruña")
    # PostGIS geometry: polygon boundary of the zone
    geom = Column(Geometry("POLYGON", srid=4326), spatial_index=True)
    centroid = Column(Geometry("POINT", srid=4326), spatial_index=True)
    altitude_min = Column(Float, index=True)
    altitude_max = Column(Float, index=True)
    altitude_mean = Column(Float, index=True)
    area_km2 = Column(Float)
    description = Column(Text)

    # Relationships
    weather_stations = relationship("WeatherStation", back_populates="zone")
    routes = relationship("RunningRoute", back_populates="zone")

    def __repr__(self):
        return f"<Zone {self.name} ({self.municipality})>"
