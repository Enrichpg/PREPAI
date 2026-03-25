import asyncio
from sqlalchemy import select, func
from app.db.database import SyncSessionLocal
from app.models.routes import RunningRoute
from app.models.zones import Zone
from geoalchemy2.elements import WKTElement

def update_existing_routes():
    db = SyncSessionLocal()
    try:
        routes = db.execute(select(RunningRoute).where(RunningRoute.municipality == None)).scalars().all()
        print(f"Updating {len(routes)} routes...")
        for route in routes:
            # Find nearest zone
            start_wkt = f"POINT({route.start_point.x if hasattr(route.start_point, 'x') else 0} {route.start_point.y if hasattr(route.start_point, 'y') else 0})"
            # Wait, start_point is a Geometry. In SQLAlchemy/GeoAlchemy it might be a bit different.
            
            zone_query = select(Zone).order_by(
                func.ST_Distance(
                    Zone.geom,
                    route.start_point
                )
            ).limit(1)
            zone = db.execute(zone_query).scalar_one_or_none()
            if zone:
                route.zone_id = zone.id
                route.municipality = zone.municipality
                print(f"Assigned route {route.id} to {zone.municipality}")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_routes()
