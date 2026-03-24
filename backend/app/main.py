from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes.weather import router as weather_router
from app.api.routes.routes_api import router as routes_router
from app.api.routes.ml_api import router as ml_router
from app.api.routes.zones import router as zones_router
from app.api.routes.external_apis import router as external_apis_router

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para recomendación de rutas de running en A Coruña basada en datos meteorológicos",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response


# Routers
app.include_router(weather_router, prefix="/api/v1")
app.include_router(routes_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(zones_router, prefix="/api/v1")
app.include_router(external_apis_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/v1/status")
async def status():
    """Detailed system status including data freshness."""
    from app.db.database import AsyncSessionLocal
    from app.models.weather import DataIngestionLog, WeatherObservation
    from sqlalchemy import select, func

    status_info = {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "error",
        "last_weather_update": None,
        "total_observations": 0,
        "model_version": None,
    }

    try:
        async with AsyncSessionLocal() as db:
            # Test DB connection
            result = await db.execute(
                select(func.max(DataIngestionLog.finished_at)).where(
                    DataIngestionLog.status == "success"
                )
            )
            last_update = result.scalar_one_or_none()
            status_info["last_weather_update"] = last_update.isoformat() if last_update else None

            count_result = await db.execute(select(func.count(WeatherObservation.id)))
            status_info["total_observations"] = count_result.scalar_one()
            status_info["database"] = "ok"
    except Exception as e:
        logger.error(f"Status check DB error: {e}")

    try:
        from app.services.ml.comfort_model import get_comfort_model
        model = get_comfort_model()
        status_info["model_version"] = model.version
    except Exception:
        pass

    return status_info


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Pre-load ML model at startup
    try:
        from app.services.ml.comfort_model import get_comfort_model
        model = get_comfort_model()
        if model.model is None:
            logger.info("No trained model found — training on synthetic data...")
            from app.db.database import SyncSessionLocal
            db = SyncSessionLocal()
            try:
                model.train(db)
            finally:
                db.close()
    except Exception as e:
        logger.warning(f"Could not load/train model at startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down PREPAI API")
