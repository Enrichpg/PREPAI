
import asyncio
from sqlalchemy.orm import Session
from app.db.database import SyncSessionLocal
from app.models.routes import RunningRoute, SurfaceType, ElevationProfile
from sqlalchemy import select, delete, func

def bootstrap_premium_routes():
    db = SyncSessionLocal()
    try:
        # 1. Clean up "noisy" routes (< 500m)
        stmt = delete(RunningRoute).where(RunningRoute.distance_km < 0.5)
        res = db.execute(stmt)
        db.commit()
        print(f"Deleted {res.rowcount} noisy segments.")

        # 2. Helper to create route
        def add_route(name, desc, dist, gain, surface, elev, coords, is_loop=False):
            coords_str = ", ".join(f"{c[0]} {c[1]}" for c in coords)
            geom_wkt = f"LINESTRING({coords_str})"
            start_wkt = f"POINT({coords[0][0]} {coords[0][1]})"
            end_wkt = f"POINT({coords[-1][0]} {coords[-1][1]})"
            
            route = RunningRoute(
                name=name,
                description=desc,
                distance_km=dist,
                elevation_gain=gain,
                surface_type=surface,
                elevation_profile=elev,
                geom=func.ST_GeomFromText(geom_wkt, 4326),
                start_point=func.ST_GeomFromText(start_wkt, 4326),
                end_point=func.ST_GeomFromText(end_wkt, 4326),
                is_loop=is_loop,
                is_verified=True,
                municipality="A Coruña",
                source="manual_gold"
            )
            db.add(route)

        # Paseo Marítimo (13.2km)
        add_route(
            "Paseo Marítimo de A Coruña",
            "La ruta running más emblemática de la ciudad, bordeando todo el litoral.",
            13.2, 45, SurfaceType.ASPHALT, ElevationProfile.FLAT,
            [[-8.4124, 43.3644], [-8.4200, 43.3680], [-8.4260, 43.3750], 
             [-8.4150, 43.3850], [-8.4000, 43.3820], [-8.3850, 43.3750], [-8.3800, 43.3600]]
        )

        # Parque de Bens (5.4km)
        add_route(
            "Circuito Parque de Bens",
            "Ruta de trail suave con vistas espectaculares al Atlántico y mucha zona verde.",
            5.4, 120, SurfaceType.TRAIL, ElevationProfile.MODERATE,
            [[-8.4420, 43.3680], [-8.4450, 43.3700], [-8.4500, 43.3680], 
             [-8.4480, 43.3650], [-8.4420, 43.3680]],
            is_loop=True
        )

        # Torre de Hércules (3.5km)
        add_route(
            "Vuelta a la Torre de Hércules",
            "Entrenamiento histórico alrededor del faro romano más antiguo del mundo.",
            3.5, 35, SurfaceType.MIXED, ElevationProfile.FLAT,
            [[-8.4060, 43.3850], [-8.4040, 43.3880], [-8.4000, 43.3860], 
             [-8.3980, 43.3820], [-8.4060, 43.3850]],
            is_loop=True
        )

        db.commit()
        print("Premium routes bootstrapped successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error bootstrapping: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    bootstrap_premium_routes()
