from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Postgres
    POSTGRES_USER: str = "prepai"
    POSTGRES_PASSWORD: str = "prepai_secure_password"
    POSTGRES_DB: str = "prepai_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    # MeteoGalicia
    METEOGALICIA_API_KEY: str = "your_meteogalicia_api_key_here"
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

    # External APIs
    AEMET_API_KEY: str = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJlbnJpcXVlLnBhcmRvLmFiQGdtYWlsLmNvbSIsImp0aSI6Ijk3NjZiMDVkLWNmZWYtNDEyMy05ZDc1LWFiODAyYzBiYWIxZCIsImlzcyI6IkFFTUVUIiwiaWF0IjoxNzczNzY0NTEwLCJ1c2VySWQiOiI5NzY2YjA1ZC1jZmVmLTQxMjMtOWQ3NS1hYjgwMmMwYmFiMWQiLCJyb2xlIjoiIn0.lBkGtZ3Izr5xcow6hoaJcR5NRRy2806PfrxDIji7veI"
    OPENWEATHER_API_KEY: str = ""
    AQICN_API_KEY: str = ""
    EVENTBRITE_API_KEY: str = ""
    TOMTOM_API_KEY: str = ""
    MAPBOX_TOKEN: str = ""

    # Paths
    MODEL_PATH: str = "/app/data/models"
    DATA_PATH: str = "/app/data"

    # AEMET
    AEMET_BASE_URL: str = "https://opendata.aemet.es/opendata/api"

    # MeteoGalicia (eliminado)

    # Overpass API (OSM)
    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    AQICN_BASE_URL: str = "https://api.waqi.info"
    EVENTBRITE_BASE_URL: str = "https://www.eventbriteapi.com/v3"
    TOMTOM_BASE_URL: str = "https://api.tomtom.com/traffic/services/4"

    # Rate limits
    API_RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
