"""
Import OSM routes into the DB, enriching with elevation data.
"""
import asyncio
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from loguru import logger
from geoalchemy2.elements import WKTElement

from app.models.routes import RunningRoute, SurfaceType, ElevationProfile
from app.models.zones import Zone
from app.services.routes.osm_client import OverpassClient, parse_osm_element
from app.services.routes.elevation import (
    get_elevation_for_route, compute_elevation_stats, classify_elevation_profile
)
from sqlalchemy import func


async def import_osm_routes(db: Session) -> int:
    """Fetch all OSM running routes for all zones and store in DB."""
    imported = 0

    # Get all zones from DB to iterate over them
    zones = db.execute(select(Zone)).scalars().all()
    logger.info(f"Starting OSM import for {len(zones)} zones")

    async with OverpassClient() as client:
        for zone in zones:
            logger.info(f"Importing routes for zone: {zone.name}")
            # Get bbox for the zone (using a buffer around its centroid or geometry)
            # For simplicity, we'll use a 10km buffer (0.1 deg) around the centroid if no bbox is stored
            # (In a real app, we'd use the actual polygon bbox)
            
            from geoalchemy2.shape import to_shape
            centroid = to_shape(zone.centroid)
            buffer = 0.08 # ~8-10km
            bbox = (centroid.y - buffer, centroid.x - buffer, centroid.y + buffer, centroid.x + buffer)
            
            raw_elements = await client.get_running_routes(bbox=bbox)
            
            for elem in raw_elements:
                try:
                    parsed = parse_osm_element(elem)
                    if not parsed:
                        continue

                    # Check for duplicates
                    existing = db.execute(
                        select(RunningRoute).where(RunningRoute.osm_id == parsed["osm_id"])
                    ).scalar_one_or_none()
                    if existing:
                        continue

                    # Fetch elevation
                    coords = parsed["coords"]
                    elevation_profile_data = await get_elevation_for_route(coords)
                    elev_stats = compute_elevation_stats(elevation_profile_data)

                    # Build WKT LineString
                    coords_str = ", ".join(f"{lon} {lat}" for lon, lat in coords)
                    geom_wkt = f"LINESTRING({coords_str})"
                    start_wkt = f"POINT({coords[0][0]} {coords[0][1]})"
                    end_wkt = f"POINT({coords[-1][0]} {coords[-1][1]})"

                    surface_map = {
                        "asphalt": SurfaceType.ASPHALT,
                        "trail": SurfaceType.TRAIL,
                        "mixed": SurfaceType.MIXED,
                    }
                    surface_type = surface_map.get(parsed.get("surface", "mixed"), SurfaceType.MIXED)

                    elev_profile_str = classify_elevation_profile(elev_stats["gain"], parsed["distance_km"])
                    elev_profile_map = {
                        "flat": ElevationProfile.FLAT,
                        "moderate": ElevationProfile.MODERATE,
                        "hilly": ElevationProfile.HILLY,
                    }
                    elev_profile = elev_profile_map.get(elev_profile_str, ElevationProfile.FLAT)

                    # Estimate duration at 6 min/km pace
                    est_duration = int(parsed["distance_km"] * 6)

                    # Find nearest zone for the route (using start point)
                    zone_query = select(Zone).order_by(
                        func.ST_Distance(
                            Zone.geom,
                            WKTElement(start_wkt, srid=4326)
                        )
                    ).limit(1)
                    zone = db.execute(zone_query).scalar_one_or_none()

                    route = RunningRoute(
                        osm_id=parsed["osm_id"],
                        name=parsed["name"],
                        geom=WKTElement(geom_wkt, srid=4326),
                        start_point=WKTElement(start_wkt, srid=4326),
                        end_point=WKTElement(end_wkt, srid=4326),
                        distance_km=parsed["distance_km"],
                        elevation_gain=elev_stats["gain"],
                        elevation_loss=elev_stats["loss"],
                        elevation_min=elev_stats["min"],
                        elevation_max=elev_stats["max"],
                        estimated_duration_min=est_duration,
                        surface_type=surface_type,
                        elevation_profile=elev_profile,
                        zone_id=zone.id if zone else None,
                        municipality=zone.municipality if zone else parsed.get("municipality"),
                        is_loop=(
                            abs(coords[0][0] - coords[-1][0]) < 0.001 and
                            abs(coords[0][1] - coords[-1][1]) < 0.001
                        ),
                        elevation_data=elevation_profile_data,
                        tags=parsed["tags"],
                        source="osm",
                    )
                    db.add(route)
                    db.commit()
                    imported += 1
                except Exception as e:
                    logger.error(f"Failed to import OSM route {elem.get('id')}: {e}")
                    db.rollback()

    logger.info(f"Imported {imported} new routes from OSM")
    return imported
