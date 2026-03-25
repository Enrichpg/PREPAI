import asyncio
import os
import sys
from sqlalchemy import text
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon, Point, LineString
from loguru import logger

# Add backend and parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import AsyncSessionLocal, sync_engine
from app.models.zones import Zone
from app.models.weather import WeatherStation, DataSource
from app.models.routes import RunningRoute, SurfaceType, ElevationProfile
from app.services.weather.aemet_client import AEMETClient
from app.services.routes.osm_client import OverpassClient
from app.services.routes.elevation import get_elevation_for_route, compute_elevation_stats, classify_elevation_profile
from app.core.config import settings

# A Coruña Zones [Name, Polygon_Coords (lon, lat)]
ZONES_DATA = [
    ("Paseo Marítimo", [
        (-8.415, 43.375), (-8.395, 43.385), (-8.380, 43.375), 
        (-8.390, 43.365), (-8.410, 43.365), (-8.415, 43.375)
    ], "Ruta icónica bordeando el océano."),
    ("Torre de Hércules", [
        (-8.410, 43.385), (-8.400, 43.395), (-8.390, 43.385),
        (-8.400, 43.375), (-8.410, 43.385)
    ], "Entorno del faro romano, Patrimonio de la Humanidad."),
    ("Parque de Bens", [
        (-8.450, 43.365), (-8.435, 43.375), (-8.420, 43.365),
        (-8.435, 43.355), (-8.450, 43.365)
    ], "Antiguo vertedero convertido en enorme parque con vistas."),
]

async def seed_zones(db):
    logger.info("Seeding Zones...")
    for name, coords, desc in ZONES_DATA:
        poly = Polygon(coords)
        zone = Zone(
            name=name,
            municipality="A Coruña",
            geom=f"POLYGON(({','.join([f'{c[0]} {c[1]}' for c in coords])}))",
            centroid=f"POINT({poly.centroid.x} {poly.centroid.y})",
            description=desc,
            area_km2=0.5 # Approximate
        )
        db.add(zone)
    await db.commit()

async def seed_stations(db):
    logger.info("Seeding Weather Stations from AEMET...")
    async with AEMETClient(api_key=settings.AEMET_API_KEY) as client:
        stations = await client.get_stations()
        for s in stations:
            # Filter for A Coruña (Province 15) or stations in the list
            if s.get("provincia") == "A CORUÑA":
                station = WeatherStation(
                    station_id=s["indicativo"],
                    name=s["nombre"],
                    municipality=s.get("municipio"),
                    province="A Coruña",
                    geom=f"POINT({s['lon'].replace(',', '.')} {s['lat'].replace(',', '.')})",
                    altitude=float(s.get("altitud", 0)),
                    source=DataSource.AEMET
                )
                db.add(station)
        await db.commit()

async def seed_routes(db):
    logger.info("Seeding Routes from OSM and Elevation...")
    async with OverpassClient() as client:
        osm_elements = await client.get_running_routes()
        from app.services.routes.osm_client import parse_osm_element
        
        count = 0
        for elem in osm_elements[:15]: # Limit to 15 for seeding
            route_data = parse_osm_element(elem)
            if not route_data: continue
            
            # Fetch elevation
            elevation_data = await get_elevation_for_route(route_data["coords"])
            stats = compute_elevation_stats(elevation_data)
            profile = classify_elevation_profile(stats["gain"], route_data["distance_km"])
            
            # Create WKT linestring
            wkt_coords = ",".join([f"{c[0]} {c[1]}" for c in route_data["coords"]])
            
            route = RunningRoute(
                osm_id=route_data["osm_id"],
                name=route_data["name"],
                geom=f"LINESTRING({wkt_coords})",
                distance_km=route_data["distance_km"],
                elevation_gain=stats["gain"],
                elevation_loss=stats["loss"],
                elevation_min=stats["min"],
                elevation_max=stats["max"],
                elevation_data=elevation_data,
                surface_type=SurfaceType.TRAIL if route_data["surface"] == "trail" else SurfaceType.ASPHALT,
                elevation_profile=ElevationProfile(profile),
                tags=route_data["tags"],
                source="osm"
            )
            db.add(route)
            count += 1
            if count >= 10: break # Seed at least 10
            
        await db.commit()

async def main():
    logger.info("Starting Database Seeding...")
    try:
        async with AsyncSessionLocal() as db:
            # 1. Enable PostGIS (requires superuser or owner with permissions)
            try:
                await db.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                await db.commit()
            except Exception as e:
                logger.warning(f"Could not enable PostGIS (might already exist): {e}")
            
            await seed_zones(db)
            await seed_stations(db)
            await seed_routes(db)
            logger.info("✅ Seeding completed successfully!")
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
