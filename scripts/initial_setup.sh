#!/bin/bash
# Initial setup script — run after docker compose up -d
set -e

echo "==> Waiting for services to be ready..."
sleep 5

echo "==> Running database migrations..."
docker compose exec backend alembic upgrade head

echo "==> Seeding zones..."
docker compose exec backend python scripts/seed_zones.py

echo "==> Importing OSM routes (background)..."
curl -s -X POST http://localhost:8000/api/v1/routes/import/osm

echo "==> Training initial ML model on synthetic data..."
curl -s -X POST http://localhost:8000/api/v1/ml/model/train

echo ""
echo "==> Setup complete!"
echo "    Frontend:  http://localhost:3000"
echo "    API docs:  http://localhost:8000/docs"
echo "    Flower:    http://localhost:5555"
echo ""
echo "    To start historical weather ingestion (may take hours):"
echo "    curl -X POST 'http://localhost:8000/api/v1/weather/ingestion/historical?years=10'"
