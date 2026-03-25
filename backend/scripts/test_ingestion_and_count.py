import asyncio
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from app.services.weather.ingestion import WeatherIngestionPipeline
from app.services.events.event_ingestion import EventIngestionPipeline
from app.services.traffic.tomtom_client import TomTomTrafficClient
from app.db.database import SyncSessionLocal

# Ajusta la fecha de entrenamiento
TRAIN_DATE = date.today()
START_DATE = TRAIN_DATE - timedelta(days=365)

# Ejecuta ingestión de weather
async def ingest_weather():
    pipeline = WeatherIngestionPipeline()
    await pipeline.ingest_aemet(START_DATE, TRAIN_DATE)
    pipeline.close()

# Ejecuta ingestión de eventos
async def ingest_events():
    pipeline = EventIngestionPipeline()
    # Usa coordenadas dummy, ajusta según tu zona
    await pipeline.ingest_events(lat=43.3623, lon=-8.4115, radius_km=10)
    pipeline.close()

# Ejecuta ingestión de tráfico (dummy, requiere implementación de pipeline)
async def ingest_traffic():
    client = TomTomTrafficClient()
    # bbox dummy, ajusta según tu zona
    await client.get_traffic_flow(bbox="-8.5,43.3,-8.3,43.4")
    await client.close()

# Cuenta registros en SQL

def count_records():
    db = SyncSessionLocal()
    queries = {
        'weather_observations': f"SELECT COUNT(*) FROM weather_observations WHERE observed_at >= '{START_DATE}' AND observed_at <= '{TRAIN_DATE}'",
        'events': f"SELECT COUNT(*) FROM events WHERE start_time >= '{START_DATE}' AND start_time <= '{TRAIN_DATE}'",
        'traffic_data': f"SELECT COUNT(*) FROM traffic_data WHERE timestamp >= '{START_DATE}' AND timestamp <= '{TRAIN_DATE}'",
    }
    for table, query in queries.items():
        result = db.execute(text(query)).scalar()
        print(f"{table}: {result} registros")
    db.close()

async def main():
    print("Ingestando weather...")
    await ingest_weather()
    print("Ingestando eventos...")
    await ingest_events()
    print("Ingestando tráfico...")
    await ingest_traffic()
    print("Contando registros...")
    count_records()

if __name__ == "__main__":
    asyncio.run(main())
