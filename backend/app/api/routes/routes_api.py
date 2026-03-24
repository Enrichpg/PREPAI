from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from typing import List, Optional
import secrets
from loguru import logger

from app.db.database import get_db
from app.models.routes import RunningRoute, SurfaceType, ElevationProfile
from app.models.recommendations import RouteRecommendation, SavedRoute
from app.schemas.routes import (
    RouteOut, RouteRecommendationRequest, RouteRecommendationOut,
    SaveRouteRequest, SavedRouteOut, WeatherWarning
)

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/", response_model=List[RouteOut])
async def list_routes(
    surface: Optional[SurfaceType] = None,
    elevation: Optional[ElevationProfile] = None,
    min_distance: Optional[float] = Query(default=None, ge=0),
    max_distance: Optional[float] = Query(default=None, le=200),
    municipality: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List running routes with optional filters."""
    query = select(RunningRoute)
    if surface:
        query = query.where(RunningRoute.surface_type == surface)
    if elevation:
        query = query.where(RunningRoute.elevation_profile == elevation)
    if min_distance is not None:
        query = query.where(RunningRoute.distance_km >= min_distance)
    if max_distance is not None:
        query = query.where(RunningRoute.distance_km <= max_distance)
    if municipality:
        query = query.where(RunningRoute.municipality.ilike(f"%{municipality}%"))

    query = query.order_by(RunningRoute.name).limit(limit).offset(offset)
    result = await db.execute(query)
    routes = result.scalars().all()

    return [_route_to_out(r) for r in routes]


@router.get("/{route_id}", response_model=RouteOut)
async def get_route(route_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details of a single route."""
    result = await db.execute(select(RunningRoute).where(RunningRoute.id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    return _route_to_out(route)


@router.post("/recommend", response_model=List[RouteRecommendationOut])
async def recommend_routes(
    request: RouteRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Get top route recommendations based on user preferences and weather forecast.
    """
    from app.db.database import SyncSessionLocal
    from app.services.routes.recommendation import RecommendationEngine

    # Use sync session for the recommendation engine (it uses sync SQLAlchemy)
    sync_db = SyncSessionLocal()
    try:
        engine = RecommendationEngine(sync_db)
        results = engine.recommend(request)
    finally:
        sync_db.close()

    output = []
    for item in results:
        route = item["route"]
        output.append(RouteRecommendationOut(
            route=_route_to_out(route),
            comfort_score=item["comfort_score"],
            match_score=item["match_score"],
            overall_score=item["overall_score"],
            rank=item["rank"],
            weather_summary=item["weather_summary"],
            warnings=item["warnings"],
            hourly_comfort=item["weather_hours"],
        ))

    return output


@router.get("/near", response_model=List[RouteOut])
async def routes_near(
    lat: float = Query(..., ge=42.0, le=44.0),
    lon: float = Query(..., ge=-9.5, le=-7.5),
    radius_km: float = Query(default=10.0, ge=0.5, le=50),
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Find routes near a given point."""
    query = text("""
        SELECT r.*, ST_Distance(
            r.start_point::geography,
            ST_GeogFromText('POINT(' || :lon || ' ' || :lat || ')')
        ) AS dist_m
        FROM running_routes r
        WHERE ST_DWithin(
            r.start_point::geography,
            ST_GeogFromText('POINT(' || :lon || ' ' || :lat || ')'),
            :radius_m
        )
        ORDER BY dist_m
        LIMIT :limit
    """)
    result = await db.execute(query, {
        "lat": lat, "lon": lon,
        "radius_m": radius_km * 1000,
        "limit": limit,
    })
    route_ids = [row[0] for row in result.fetchall()]

    routes = []
    for rid in route_ids:
        res = await db.execute(select(RunningRoute).where(RunningRoute.id == rid))
        r = res.scalar_one_or_none()
        if r:
            routes.append(_route_to_out(r))
    return routes


@router.post("/saved", response_model=SavedRouteOut)
async def save_route(
    request: SaveRouteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Save a route to user's favourites."""
    result = await db.execute(select(RunningRoute).where(RunningRoute.id == request.route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    saved = SavedRoute(
        route_id=request.route_id,
        session_id=request.session_id,
        nickname=request.nickname,
        notes=request.notes,
        share_token=secrets.token_urlsafe(32),
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)

    return SavedRouteOut(
        id=saved.id,
        route_id=saved.route_id,
        session_id=saved.session_id,
        nickname=saved.nickname,
        notes=saved.notes,
        share_token=saved.share_token,
        created_at=saved.created_at,
        route=_route_to_out(route),
    )


@router.get("/saved/{session_id}", response_model=List[SavedRouteOut])
async def get_saved_routes(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all saved routes for a session."""
    result = await db.execute(
        select(SavedRoute).where(SavedRoute.session_id == session_id)
        .order_by(SavedRoute.created_at.desc())
    )
    saved = result.scalars().all()

    out = []
    for s in saved:
        route_result = await db.execute(select(RunningRoute).where(RunningRoute.id == s.route_id))
        route = route_result.scalar_one_or_none()
        out.append(SavedRouteOut(
            id=s.id,
            route_id=s.route_id,
            session_id=s.session_id,
            nickname=s.nickname,
            notes=s.notes,
            share_token=s.share_token,
            created_at=s.created_at,
            route=_route_to_out(route) if route else None,
        ))
    return out


@router.get("/shared/{share_token}", response_model=SavedRouteOut)
async def get_shared_route(share_token: str, db: AsyncSession = Depends(get_db)):
    """View a shared route by token."""
    result = await db.execute(select(SavedRoute).where(SavedRoute.share_token == share_token))
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Enlace compartido no válido")

    route_result = await db.execute(select(RunningRoute).where(RunningRoute.id == saved.route_id))
    route = route_result.scalar_one_or_none()

    return SavedRouteOut(
        id=saved.id,
        route_id=saved.route_id,
        session_id=saved.session_id,
        nickname=saved.nickname,
        notes=saved.notes,
        share_token=saved.share_token,
        created_at=saved.created_at,
        route=_route_to_out(route) if route else None,
    )


@router.post("/import/osm")
async def import_osm(background_tasks: BackgroundTasks):
    """Trigger OSM route import in the background."""
    from app.db.database import SyncSessionLocal
    from app.services.routes.importer import import_osm_routes

    async def run_import():
        sync_db = SyncSessionLocal()
        try:
            count = await import_osm_routes(sync_db)
            logger.info(f"OSM import complete: {count} routes")
        finally:
            sync_db.close()

    background_tasks.add_task(run_import)
    return {"message": "Importación OSM iniciada en segundo plano"}


def _route_to_out(route: RunningRoute) -> RouteOut:
    geojson = None
    if route.geom is not None:
        try:
            from geoalchemy2.shape import to_shape
            shape = to_shape(route.geom)
            geojson = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": list(shape.coords),
                },
                "properties": {"id": route.id, "name": route.name},
            }
        except Exception:
            pass

    return RouteOut(
        id=route.id,
        osm_id=route.osm_id,
        name=route.name,
        description=route.description,
        distance_km=route.distance_km,
        elevation_gain=route.elevation_gain,
        elevation_loss=route.elevation_loss,
        elevation_min=route.elevation_min,
        elevation_max=route.elevation_max,
        estimated_duration_min=route.estimated_duration_min,
        surface_type=route.surface_type,
        elevation_profile=route.elevation_profile,
        difficulty=route.difficulty,
        is_loop=route.is_loop,
        municipality=route.municipality,
        zone_id=route.zone_id,
        is_verified=route.is_verified,
        elevation_data=route.elevation_data,
        tags=route.tags,
        geojson=geojson,
    )
