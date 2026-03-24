# PREPAI — Recomendador de Rutas de Running · A Coruña

Sistema full-stack de recomendación de rutas de running para la provincia de A Coruña (Galicia) basado en datos meteorológicos históricos y en tiempo real, con un modelo de ML que predice la comodidad de correr.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND (React)                      │
│  Leaflet Map │ SearchForm │ RouteCards │ Dashboard │ Charts  │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  /weather  │  /routes  │  /ml  │  /zones                    │
└──────┬─────────────┬────────────────┬───────────────────────┘
       │             │                │
┌──────▼──────┐ ┌────▼────┐  ┌───────▼──────────────────────┐
│ PostgreSQL  │ │  Redis  │  │  Celery Workers               │
│ + PostGIS   │ │ (cache/ │  │  - weather ingestion          │
│             │ │  queue) │  │  - ML retraining              │
│  Obs / Fore │ └─────────┘  │  - forecast refresh           │
│  Routes     │              └──────────────────────────────┘
└─────────────┘

External APIs:
  AEMET OpenData  →  historical obs + forecasts
  MeteoGalicia    →  regional obs + forecasts
  OSM Overpass    →  running routes / paths
  Open-Elevation  →  elevation profiles (SRTM)
```

---

## Requisitos previos

- Docker ≥ 24 + Docker Compose ≥ 2.20
- API keys (gratuitas):
  - [AEMET OpenData](https://opendata.aemet.es/centrodedescargas/altaUsuario?) — registro gratuito
  - MeteoGalicia — sin key (API pública)

---

## Puesta en marcha rápida

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd PREPAI

# 2. Crear archivo de entorno
cp .env.example .env
# Editar .env y rellenar AEMET_API_KEY

# 3. Levantar todos los servicios
docker compose up -d

# 4. Aplicar migraciones de base de datos
docker compose exec backend alembic upgrade head

# 5. Crear zonas iniciales de A Coruña (script de seed)
docker compose exec backend python scripts/seed_zones.py

# 6. Importar rutas desde OpenStreetMap
curl -X POST http://localhost:8000/api/v1/routes/import/osm

# 7. (Opcional) Ingestar datos históricos de los últimos 10 años
curl -X POST "http://localhost:8000/api/v1/weather/ingestion/historical?years=10"

# 8. Entrenar el modelo ML
curl -X POST http://localhost:8000/api/v1/ml/model/train

# Frontend disponible en: http://localhost:3000
# API docs en:             http://localhost:8000/docs
# Monitor Celery (Flower): http://localhost:5555
```

---

## Estructura del proyecto

```
PREPAI/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Endpoints FastAPI
│   │   │   ├── weather.py       # /weather/*
│   │   │   ├── routes_api.py    # /routes/*
│   │   │   ├── ml_api.py        # /ml/*
│   │   │   └── zones.py         # /zones/*
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   └── celery_app.py    # Celery + beat schedule
│   │   ├── db/database.py       # SQLAlchemy async engine
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── weather.py       # WeatherStation, WeatherObservation, WeatherForecast
│   │   │   ├── routes.py        # RunningRoute, RouteSegment
│   │   │   ├── recommendations.py
│   │   │   └── zones.py
│   │   ├── schemas/             # Pydantic schemas (request/response)
│   │   ├── services/
│   │   │   ├── weather/
│   │   │   │   ├── aemet_client.py       # AEMET API client
│   │   │   │   ├── meteogalicia_client.py# MeteoGalicia API client
│   │   │   │   ├── ingestion.py          # ETL pipeline
│   │   │   │   ├── forecast_processor.py # Forecast normalisation
│   │   │   │   └── tasks.py              # Celery tasks
│   │   │   ├── ml/
│   │   │   │   ├── comfort_model.py      # XGBoost comfort model
│   │   │   │   └── tasks.py              # Celery retraining task
│   │   │   └── routes/
│   │   │       ├── osm_client.py         # Overpass API client
│   │   │       ├── elevation.py          # Elevation fetching
│   │   │       ├── recommendation.py     # Scoring engine
│   │   │       └── importer.py           # OSM → DB importer
│   │   └── main.py
│   ├── migrations/              # Alembic migrations
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_comfort_model.py
│   │   │   ├── test_weather_parsers.py
│   │   │   └── test_recommendation_engine.py
│   │   └── integration/
│   │       └── test_api_health.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Map/MapView.tsx        # Leaflet map + heatmap + route polylines
│       │   ├── Filters/SearchForm.tsx # Search/filter panel
│       │   ├── Routes/RouteCard.tsx   # Route recommendation card
│       │   ├── Routes/ElevationChart.tsx
│       │   ├── Routes/HourlyComfortChart.tsx
│       │   ├── Dashboard/WeatherDashboard.tsx
│       │   └── UI/                    # Shared UI components
│       ├── hooks/                     # useRecommendations, useWeather
│       ├── pages/                     # HomePage, SharedRoutePage
│       ├── services/api.ts            # Axios API client
│       ├── types/index.ts             # TypeScript types
│       └── utils/                     # comfort.ts, session.ts
├── data/
│   ├── raw/        # Downloaded raw data files
│   ├── processed/  # Processed DataFrames
│   └── models/     # Trained model files (.joblib)
├── scripts/
│   └── init_db.sql
├── nginx/nginx.conf
├── docker-compose.yml
└── .env.example
```

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `AEMET_API_KEY` | Key de AEMET OpenData | Sí |
| `METEOGALICIA_API_KEY` | Key de MeteoGalicia (actualmente no requerida) | No |
| `POSTGRES_USER` | Usuario de PostgreSQL | Sí |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | Sí |
| `POSTGRES_DB` | Nombre de la base de datos | Sí |
| `DATABASE_URL` | URL completa de conexión | Sí |
| `REDIS_URL` | URL de Redis | Sí |
| `SECRET_KEY` | Clave secreta de la aplicación | Sí |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | Sí |
| `MODEL_PATH` | Ruta donde guardar modelos ML | No |
| `DEBUG` | Activar modo debug | No |

---

## API endpoints principales

### Weather
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/weather/stations` | Listar estaciones meteorológicas |
| GET | `/api/v1/weather/forecasts/{zone_id}` | Previsión horaria por zona |
| GET | `/api/v1/weather/heatmap` | Puntuaciones de comodidad para mapa de calor |
| GET | `/api/v1/weather/historical/stats` | Estadísticas históricas mensuales |
| GET | `/api/v1/weather/ingestion/logs` | Registro de ingestas de datos |
| POST | `/api/v1/weather/ingestion/trigger` | Disparar ingesta semanal |
| POST | `/api/v1/weather/ingestion/historical` | Disparar ingesta histórica |

### Routes
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/routes/` | Listar rutas con filtros |
| GET | `/api/v1/routes/{id}` | Detalle de una ruta |
| POST | `/api/v1/routes/recommend` | Recibir recomendaciones personalizadas |
| GET | `/api/v1/routes/near` | Rutas cerca de una ubicación |
| POST | `/api/v1/routes/saved` | Guardar ruta favorita |
| GET | `/api/v1/routes/saved/{session_id}` | Rutas guardadas de una sesión |
| GET | `/api/v1/routes/shared/{token}` | Ver ruta compartida |
| POST | `/api/v1/routes/import/osm` | Importar rutas de OpenStreetMap |

### ML
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/ml/model/metrics` | Métricas del modelo actual |
| POST | `/api/v1/ml/model/train` | Disparar reentrenamiento |
| POST | `/api/v1/ml/predict/comfort` | Predicción puntual de comodidad |

---

## Pipeline de datos

```
Lunes 03:00 AM  →  Celery Beat dispara fetch_all_weather_data
                   ├── AEMET: fetch últimos 8 días por estación
                   └── MeteoGalicia: fetch últimos 8 días por estación

Lunes 06:00 AM  →  Celery Beat dispara retrain_model
                   ├── Carga observations de los últimos 10 años
                   ├── Feature engineering (20 variables)
                   ├── Entrena XGBoost con early stopping
                   └── Guarda modelo + métricas en /data/models/

Diario 05:00 AM →  Celery Beat dispara refresh_forecasts
                   ├── AEMET: forecast 7 días todos municipios
                   ├── MeteoGalicia: forecast concellos A Coruña
                   └── Actualiza comfort_score en weather_forecasts
```

---

## Modelo ML

El modelo predice una puntuación de comodidad (0-100) basándose en:

**Variables de entrada:**
- Temperatura, humedad, precipitación, probabilidad de precipitación
- Velocidad y racha de viento
- Cobertura nube, presión, índice UV, radiación solar
- Presencia de niebla
- Codificación cíclica de hora del día y mes del año
- Variables derivadas: desviación de temperatura ideal, penalización de humedad, índice de calor

**Algoritmo:** XGBoost Regressor con early stopping

**Target:** Score heurístico (0-100) generado a partir de reglas climatológicas de comodidad para correr (temperatura ideal 8-18°C, baja precipitación, viento moderado, sin niebla, UV bajo-moderado)

---

## Tests

```bash
# Backend
cd backend
pip install -r requirements.txt
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=app --cov-report=html
```

---

## Desarrollo local (sin Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # editar .env
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm start
```

---

## Fuentes de datos

| Fuente | URL | Uso |
|---|---|---|
| AEMET OpenData | https://opendata.aemet.es | Observaciones históricas + previsiones |
| MeteoGalicia | https://servizos.meteogalicia.gal/apiv4 | Observaciones regionales + previsiones |
| OpenStreetMap Overpass | https://overpass-api.de | Rutas de running / senderos |
| Open-Elevation | https://api.open-elevation.com | Perfiles de altitud (SRTM) |
