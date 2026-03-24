"""
AEMET OpenData API client.
Docs: https://opendata.aemet.es/dist/index.html
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

from app.core.config import settings


# A Coruña province station IDs (AEMET indicativos)
ACORUNA_STATIONS = [
    "1387", "1387E", "1394", "1428", "1428A", "1428B",
    "1431", "1432", "1432A", "1432X", "1434", "1434B",
    "1452A", "1452C", "1452E", "1452H", "1462", "1462A",
    "1462E", "1464", "1472", "1472A", "1472B", "1475",
    "1475A", "1484", "1484B", "1484C", "1485", "1485A",
    "1486", "1487", "1488A", "1489", "1495", "1495A",
    "1495C", "1495E", "1496", "1497", "1498", "1499",
]


class AEMETClient:
    BASE_URL = settings.AEMET_BASE_URL

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.AEMET_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=httpx.Timeout(30.0),
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _get_data_url(self, endpoint: str) -> Optional[str]:
        """AEMET uses a two-step pattern: first get a data URL, then fetch it."""
        url = f"{self.BASE_URL}{endpoint}"
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()
        if data.get("estado") == 200:
            return data.get("datos")
        logger.warning(f"AEMET endpoint {endpoint} returned estado={data.get('estado')}: {data.get('descripcion')}")
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _fetch_data(self, data_url: str) -> Optional[Any]:
        resp = await self._client.get(data_url)
        resp.raise_for_status()
        return resp.json()

    async def get_stations(self) -> List[Dict]:
        """Fetch all AEMET stations in A Coruña."""
        data_url = await self._get_data_url("/valores/climatologicos/inventarioestaciones/todasestaciones/")
        if not data_url:
            return []
        stations = await self._fetch_data(data_url)
        # Filter to A Coruña province (provincia code 15)
        return [s for s in (stations or []) if s.get("provincia", "").upper() == "A CORUÑA"]

    async def get_historical_observations(
        self, station_id: str, start: date, end: date
    ) -> List[Dict]:
        """
        Fetch hourly climate observations for a station between start and end dates.
        AEMET limits requests to 31-day windows.
        """
        all_records = []
        current = start
        while current <= end:
            window_end = min(current + timedelta(days=30), end)
            start_str = current.strftime("%Y-%m-%dT00:00:00UTC")
            end_str = window_end.strftime("%Y-%m-%dT23:59:59UTC")
            endpoint = (
                f"/observacion/convencional/datos/estacion/{station_id}/"
                f"periodo/{start_str}/{end_str}/"
            )
            try:
                data_url = await self._get_data_url(endpoint)
                if data_url:
                    records = await self._fetch_data(data_url)
                    if records:
                        all_records.extend(records)
                # AEMET rate-limit: max 1 req/s
                await asyncio.sleep(1.1)
            except Exception as e:
                logger.error(f"Error fetching AEMET station {station_id} {current}: {e}")
            current = window_end + timedelta(days=1)
        return all_records

    async def get_forecast_municipality(self, municipality_code: str) -> Optional[Dict]:
        """Fetch hourly forecast for a municipality (INE code)."""
        endpoint = f"/prediccion/especifica/municipio/horaria/{municipality_code}/"
        data_url = await self._get_data_url(endpoint)
        if not data_url:
            return None
        return await self._fetch_data(data_url)

    async def get_forecast_all_acoruna(self) -> List[Dict]:
        """Fetch forecasts for all A Coruña municipalities."""
        # A Coruña INE codes: 15001-15930 range
        # We use the provincial forecast endpoint
        endpoint = "/prediccion/provincia/15/mañana/"
        data_url = await self._get_data_url(endpoint)
        if not data_url:
            return []
        data = await self._fetch_data(data_url)
        return data if isinstance(data, list) else []

    async def get_uv_index(self) -> Optional[Dict]:
        """Fetch UV index forecast."""
        data_url = await self._get_data_url("/prediccion/especifica/uvi/0/")
        if not data_url:
            return None
        return await self._fetch_data(data_url)


def parse_aemet_observation(raw: Dict, station_id: str) -> Optional[Dict]:
    """Parse a raw AEMET observation record into a normalised dict."""
    try:
        def _float(val):
            if val is None or val == "" or val == "Ip":
                return None
            try:
                return float(str(val).replace(",", "."))
            except (ValueError, TypeError):
                return None

        observed_at_str = raw.get("fint") or raw.get("fecha")
        if not observed_at_str:
            return None

        observed_at = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))

        # Wind direction: cardinal -> degrees
        wind_dir_map = {
            "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
            "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
            "S": 180, "SSO": 202.5, "SO": 225, "OSO": 247.5,
            "O": 270, "ONO": 292.5, "NO": 315, "NNO": 337.5,
            "C": 0,
        }
        wind_dir_raw = raw.get("dv") or raw.get("viento_direccion")
        wind_dir = wind_dir_map.get(str(wind_dir_raw).upper()) if wind_dir_raw else _float(wind_dir_raw)

        return {
            "station_external_id": station_id,
            "observed_at": observed_at,
            "temperature": _float(raw.get("ta") or raw.get("tmed")),
            "temperature_min": _float(raw.get("tmin")),
            "temperature_max": _float(raw.get("tmax")),
            "humidity": _float(raw.get("hr") or raw.get("hrmed")),
            "precipitation": _float(raw.get("prec") or raw.get("precipitacion")),
            "wind_speed": _float(raw.get("vv") or raw.get("velmedia")),
            "wind_gust": _float(raw.get("vmax") or raw.get("racha")),
            "wind_direction": wind_dir,
            "pressure": _float(raw.get("pres") or raw.get("presMax")),
            "visibility": _float(raw.get("vis")),
            "cloud_cover": _float(raw.get("nub")),
        }
    except Exception as e:
        logger.debug(f"Failed to parse AEMET observation: {e} — raw={raw}")
        return None
