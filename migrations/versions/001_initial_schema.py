"""Initial schema with PostGIS

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Zones
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("municipality", sa.String(200), nullable=False),
        sa.Column("comarca", sa.String(200)),
        sa.Column("province", sa.String(100), default="A Coruña"),
        sa.Column("geom", geoalchemy2.Geometry("POLYGON", srid=4326, nullable=True)),
        sa.Column("centroid", geoalchemy2.Geometry("POINT", srid=4326, nullable=True)),
        sa.Column("altitude_min", sa.Float),
        sa.Column("altitude_max", sa.Float),
        sa.Column("altitude_mean", sa.Float),
        sa.Column("area_km2", sa.Float),
        sa.Column("description", sa.Text),
    )
    op.create_index("ix_zones_name", "zones", ["name"])
    op.create_index("ix_zones_municipality", "zones", ["municipality"])

    # Weather stations
    op.create_table(
        "weather_stations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("station_id", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("municipality", sa.String(200)),
        sa.Column("province", sa.String(100)),
        sa.Column("source", sa.String(50)),
        sa.Column("geom", geoalchemy2.Geometry("POINT", srid=4326, nullable=True)),
        sa.Column("altitude", sa.Float),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_weather_stations_station_id", "weather_stations", ["station_id"])

    # Weather observations
    op.create_table(
        "weather_observations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("station_id", sa.Integer, sa.ForeignKey("weather_stations.id"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("temperature", sa.Float),
        sa.Column("temperature_min", sa.Float),
        sa.Column("temperature_max", sa.Float),
        sa.Column("feels_like", sa.Float),
        sa.Column("humidity", sa.Float),
        sa.Column("precipitation", sa.Float),
        sa.Column("precipitation_probability", sa.Float),
        sa.Column("wind_speed", sa.Float),
        sa.Column("wind_gust", sa.Float),
        sa.Column("wind_direction", sa.Float),
        sa.Column("pressure", sa.Float),
        sa.Column("visibility", sa.Float),
        sa.Column("cloud_cover", sa.Float),
        sa.Column("uv_index", sa.Float),
        sa.Column("solar_radiation", sa.Float),
        sa.Column("snow_depth", sa.Float),
        sa.Column("fog", sa.Boolean, default=False),
        sa.Column("weather_code", sa.String(20)),
        sa.Column("weather_description", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_weather_observations_station_id", "weather_observations", ["station_id"])
    op.create_index("ix_weather_observations_observed_at", "weather_observations", ["observed_at"])

    # Weather forecasts
    op.create_table(
        "weather_forecasts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("zones.id"), nullable=False),
        sa.Column("forecast_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("temperature", sa.Float),
        sa.Column("temperature_min", sa.Float),
        sa.Column("temperature_max", sa.Float),
        sa.Column("feels_like", sa.Float),
        sa.Column("humidity", sa.Float),
        sa.Column("precipitation", sa.Float),
        sa.Column("precipitation_probability", sa.Float),
        sa.Column("wind_speed", sa.Float),
        sa.Column("wind_gust", sa.Float),
        sa.Column("wind_direction", sa.Float),
        sa.Column("pressure", sa.Float),
        sa.Column("visibility", sa.Float),
        sa.Column("cloud_cover", sa.Float),
        sa.Column("uv_index", sa.Float),
        sa.Column("solar_radiation", sa.Float),
        sa.Column("fog", sa.Boolean, default=False),
        sa.Column("weather_code", sa.String(20)),
        sa.Column("weather_description", sa.String(200)),
        sa.Column("comfort_score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_weather_forecasts_zone_id", "weather_forecasts", ["zone_id"])
    op.create_index("ix_weather_forecasts_forecast_for", "weather_forecasts", ["forecast_for"])

    # Data ingestion logs
    op.create_table(
        "data_ingestion_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("task_name", sa.String(200)),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(50), default="running"),
        sa.Column("records_fetched", sa.Integer, default=0),
        sa.Column("records_inserted", sa.Integer, default=0),
        sa.Column("records_updated", sa.Integer, default=0),
        sa.Column("date_range_start", sa.DateTime(timezone=True)),
        sa.Column("date_range_end", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("metadata", sa.JSON),
    )

    # Running routes
    op.create_table(
        "running_routes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("osm_id", sa.String(100), unique=True, nullable=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("zone_id", sa.Integer, sa.ForeignKey("zones.id"), nullable=True),
        sa.Column("geom", geoalchemy2.Geometry("LINESTRING", srid=4326, nullable=True)),
        sa.Column("start_point", geoalchemy2.Geometry("POINT", srid=4326, nullable=True)),
        sa.Column("end_point", geoalchemy2.Geometry("POINT", srid=4326, nullable=True)),
        sa.Column("distance_km", sa.Float, nullable=False),
        sa.Column("elevation_gain", sa.Float),
        sa.Column("elevation_loss", sa.Float),
        sa.Column("elevation_min", sa.Float),
        sa.Column("elevation_max", sa.Float),
        sa.Column("estimated_duration_min", sa.Integer),
        sa.Column("surface_type", sa.String(50)),
        sa.Column("elevation_profile", sa.String(50)),
        sa.Column("difficulty", sa.String(20)),
        sa.Column("is_loop", sa.Boolean, default=False),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("elevation_data", sa.JSON),
        sa.Column("tags", sa.JSON),
        sa.Column("municipality", sa.String(200)),
        sa.Column("source", sa.String(50), default="osm"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_running_routes_name", "running_routes", ["name"])

    # Route segments
    op.create_table(
        "route_segments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("route_id", sa.Integer, sa.ForeignKey("running_routes.id"), nullable=False),
        sa.Column("segment_index", sa.Integer, nullable=False),
        sa.Column("geom", geoalchemy2.Geometry("LINESTRING", srid=4326, nullable=True)),
        sa.Column("distance_km", sa.Float),
        sa.Column("elevation_gain", sa.Float),
        sa.Column("surface_type", sa.String(50)),
    )

    # Route recommendations
    op.create_table(
        "route_recommendations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("route_id", sa.Integer, sa.ForeignKey("running_routes.id"), nullable=False),
        sa.Column("session_id", sa.String(100)),
        sa.Column("target_distance_km", sa.Float),
        sa.Column("target_duration_min", sa.Integer),
        sa.Column("preferred_surface", sa.String(50)),
        sa.Column("preferred_elevation", sa.String(50)),
        sa.Column("start_lat", sa.Float),
        sa.Column("start_lon", sa.Float),
        sa.Column("requested_date", sa.DateTime(timezone=True)),
        sa.Column("requested_time_start", sa.Integer),
        sa.Column("requested_time_end", sa.Integer),
        sa.Column("comfort_score", sa.Float),
        sa.Column("match_score", sa.Float),
        sa.Column("overall_score", sa.Float),
        sa.Column("rank", sa.Integer),
        sa.Column("weather_summary", sa.JSON),
        sa.Column("warnings", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Saved routes
    op.create_table(
        "saved_routes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("route_id", sa.Integer, sa.ForeignKey("running_routes.id"), nullable=False),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("nickname", sa.String(200)),
        sa.Column("notes", sa.Text),
        sa.Column("share_token", sa.String(64), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_saved_routes_session_id", "saved_routes", ["session_id"])
    op.create_index("ix_saved_routes_share_token", "saved_routes", ["share_token"])


def downgrade() -> None:
    op.drop_table("saved_routes")
    op.drop_table("route_recommendations")
    op.drop_table("route_segments")
    op.drop_table("running_routes")
    op.drop_table("data_ingestion_logs")
    op.drop_table("weather_forecasts")
    op.drop_table("weather_observations")
    op.drop_table("weather_stations")
    op.drop_table("zones")
