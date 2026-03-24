from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.models.zones import Zone

router = APIRouter(prefix="/zones", tags=["zones"])


class ZoneOut(BaseModel):
    id: int
    name: str
    municipality: str
    comarca: Optional[str] = None
    province: str
    altitude_mean: Optional[float] = None
    area_km2: Optional[float] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ZoneOut])
async def list_zones(db: AsyncSession = Depends(get_db)):
    """List all zones in A Coruña province."""
    result = await db.execute(select(Zone).order_by(Zone.municipality))
    zones = result.scalars().all()

    out = []
    for z in zones:
        lat = lon = None
        if z.centroid:
            try:
                from geoalchemy2.shape import to_shape
                pt = to_shape(z.centroid)
                lat, lon = pt.y, pt.x
            except Exception:
                pass
        out.append(ZoneOut(
            id=z.id,
            name=z.name,
            municipality=z.municipality,
            comarca=z.comarca,
            province=z.province,
            altitude_mean=z.altitude_mean,
            area_km2=z.area_km2,
            centroid_lat=lat,
            centroid_lon=lon,
        ))
    return out


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(zone_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    lat = lon = None
    if zone.centroid:
        try:
            from geoalchemy2.shape import to_shape
            pt = to_shape(zone.centroid)
            lat, lon = pt.y, pt.x
        except Exception:
            pass

    return ZoneOut(
        id=zone.id,
        name=zone.name,
        municipality=zone.municipality,
        comarca=zone.comarca,
        province=zone.province,
        altitude_mean=zone.altitude_mean,
        area_km2=zone.area_km2,
        centroid_lat=lat,
        centroid_lon=lon,
    )
