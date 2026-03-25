from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Postgres
    POSTGRES_USER: str = "prepai"
    POSTGRES_PASSWORD: str = "prepai_secure_password"
    POSTGRES_DB: str = "prepai_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    # App
    APP_NAME: str = "PREPAI - Rutas de Running A Coruña"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change_me_to_a_random_secret_key_32chars"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:80"

    # Database
    DATABASE_URL: str = "postgresql://prepai:prepai_secure_password@localhost:5432/prepai_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Active external APIs
    # 1. AEMET OpenData — API key required
    AEMET_API_KEY: str = ""
    AEMET_BASE_URL: str = "https://opendata.aemet.es/opendata/api"

    # 2. OSM Overpass — public, no key required
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"

    # 3. Open-Elevation — public, no key required
    OPEN_ELEVATION_URL: str = "https://api.open-elevation.com/api/v1/lookup"

    # Paths
    MODEL_PATH: str = "/app/data/models"
    DATA_PATH: str = "/app/data"

    # Rate limits
    API_RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
