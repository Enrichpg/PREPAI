"""
Seed initial zones for A Coruña province municipalities.
Run inside the backend container:
  docker compose exec backend python scripts/seed_zones.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SyncSessionLocal
from app.models.zones import Zone
from sqlalchemy import select
from geoalchemy2.elements import WKTElement

# Key municipalities of A Coruña with approximate centroids (lat, lon)
MUNICIPALITIES = [
    ("A Coruña", "A Coruña", "Golfo Ártabro", 43.3623, -8.4115),
    ("Santiago de Compostela", "Santiago de Compostela", "Terra de Santiago", 42.8805, -8.5457),
    ("Ferrol", "Ferrol", "Ferrolterra", 43.4843, -8.2330),
    ("Ourense", "Ourense", "Ourense", 42.3364, -7.8645),
    ("Lugo", "Lugo", "Lugo", 43.0097, -7.5560),
    ("Vigo", "Vigo", "Vigo", 42.2328, -8.7226),
    ("Pontevedra", "Pontevedra", "Pontevedra", 42.4335, -8.6483),
    ("Betanzos", "Betanzos", "Betanzos", 43.2783, -8.2115),
    ("Carballo", "Carballo", "Bergantiños", 43.2138, -8.6910),
    ("Narón", "Narón", "Ferrolterra", 43.5219, -8.1568),
    ("Oleiros", "Oleiros", "Golfo Ártabro", 43.3350, -8.3016),
    ("Culleredo", "Culleredo", "Golfo Ártabro", 43.2948, -8.3962),
    ("Cambre", "Cambre", "Golfo Ártabro", 43.2931, -8.3444),
    ("Arteixo", "Arteixo", "Golfo Ártabro", 43.3069, -8.5075),
    ("Boiro", "Boiro", "Barbanza", 42.6508, -8.8835),
    ("Ribeira", "Ribeira", "Barbanza", 42.5553, -8.9914),
    ("Noia", "Noia", "Noia", 42.7903, -8.8805),
    ("Arzúa", "Arzúa", "Terra de Melide", 42.9280, -8.1608),
    ("Melide", "Melide", "Terra de Melide", 42.9212, -8.0145),
    ("Ortigueira", "Ortigueira", "Ortegal", 43.6906, -7.8567),
    ("Cedeira", "Cedeira", "Ortegal", 43.6570, -8.0492),
    ("Viveiro", "Viveiro", "A Mariña Occidental", 43.6614, -7.5938),
    ("As Pontes", "As Pontes de García Rodríguez", "Eume", 43.4531, -7.8493),
    ("Pontedeume", "Pontedeume", "Eume", 43.4030, -8.1630),
    ("Mugardos", "Mugardos", "Ferrolterra", 43.4632, -8.2518),
    ("A Laracha", "A Laracha", "Bergantiños", 43.2473, -8.5847),
    ("Malpica de Bergantiños", "Malpica de Bergantiños", "Bergantiños", 43.3354, -8.8116),
    ("Laxe", "Laxe", "Costa da Morte", 43.2228, -9.0052),
    ("Cee", "Cee", "Costa da Morte", 42.9546, -9.1877),
    ("Fisterra", "Fisterra", "Costa da Morte", 42.9036, -9.2651),
    ("Corcubión", "Corcubión", "Costa da Morte", 42.9382, -9.1983),
    ("Muxía", "Muxía", "Costa da Morte", 43.1003, -9.2228),
    ("Camariñas", "Camariñas", "Costa da Morte", 43.1248, -9.1771),
    ("Vimianzo", "Vimianzo", "Costa da Morte", 43.1124, -9.0330),
    ("Zas", "Zas", "Costa da Morte", 43.0614, -8.9038),
    ("Santa Comba", "Santa Comba", "Terra de Santiago", 42.9814, -8.8205),
    ("Negreira", "Negreira", "Terra de Santiago", 42.9059, -8.7309),
    ("Padrón", "Padrón", "O Sar", 42.7355, -8.6562),
    ("Rianxo", "Rianxo", "Barbanza", 42.6476, -8.8153),
    ("Pobra do Caramiñal", "A Pobra do Caramiñal", "Barbanza", 42.6007, -8.9320),
]


def seed_zones():
    db = SyncSessionLocal()
    inserted = 0
    try:
        for name, municipality, comarca, lat, lon in MUNICIPALITIES:
            existing = db.execute(
                select(Zone).where(Zone.municipality == municipality)
            ).scalar_one_or_none()

            if existing:
                continue

            centroid_wkt = f"POINT({lon} {lat})"
            # Simple bounding box polygon (0.1 degree sides)
            geom_wkt = (
                f"POLYGON(({lon-0.05} {lat-0.05}, {lon+0.05} {lat-0.05}, "
                f"{lon+0.05} {lat+0.05}, {lon-0.05} {lat+0.05}, {lon-0.05} {lat-0.05}))"
            )

            zone = Zone(
                name=name,
                municipality=municipality,
                comarca=comarca,
                province="A Coruña",
                centroid=WKTElement(centroid_wkt, srid=4326),
                geom=WKTElement(geom_wkt, srid=4326),
            )
            db.add(zone)
            inserted += 1

        db.commit()
        print(f"Seeded {inserted} zones successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding zones: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_zones()
