"""
AEMET OpenData API client.
Docs: https://opendata.aemet.es/dist/index.html
Spec: https://opendata.aemet.es/AEMET_OpenData_specification.json

Authentication: api_key query parameter.
Data pattern:  GET endpoint → JSON with {"estado":200,"datos":"<url>"}
               then GET that url → actual data array.
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

from app.core.config import settings


# A Coruña province station indicativos (AEMET)
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
    BASE_URL = settings.AEMET_BASE_URL  # "https://opendata.aemet.es/opendata/api"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.AEMET_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers={"Accept": "application/json"},
            timeout=httpx.Timeout(30.0),
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    def _params(self, extra: Dict = None) -> Dict:
        """Merge api_key with any extra query params."""
        p = {"api_key": self.api_key}
        if extra:
            p.update(extra)
        return p

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _get_data_url(self, endpoint: str) -> Optional[str]:
        """
        AEMET two-step pattern:
          1. GET endpoint → {estado: 200, datos: '<signed-url>'}
          2. GET signed URL → actual data
        Returns the signed data URL if estado==200, else None.
        """
        url = f"{self.BASE_URL}{endpoint}"
        resp = await self._client.get(url, params=self._params())
        resp.raise_for_status()
        body = resp.json()
        if body.get("estado") == 200:
            return body.get("datos")
        logger.warning(
            f"AEMET {endpoint} → estado={body.get('estado')}: {body.get('descripcion')}"
        )
        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _fetch_data(self, data_url: str) -> Optional[Any]:
        """Fetch the signed data URL returned in step 1."""
        import json
        resp = await self._client.get(data_url)
        resp.raise_for_status()
        
        try:
            # Try UTF-8 first
            content = resp.content.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to Latin-1 (common for AEMET)
            content = resp.content.decode("iso-8859-1")
            
        return json.loads(content)

    # ─────────────────────────────────────────
    # Stations
    # ─────────────────────────────────────────

    async def get_stations(self) -> List[Dict]:
        """
        GET /api/valores/climatologicos/inventarioestaciones/todasestaciones
        Returns all AEMET stations filtered to A Coruña province.
        """
        data_url = await self._get_data_url(
            "/valores/climatologicos/inventarioestaciones/todasestaciones/"
        )
        if not data_url:
            return []
        stations = await self._fetch_data(data_url) or []
        return [s for s in stations if s.get("provincia", "").upper() == "A CORUÑA"]

    # ─────────────────────────────────────────
    # Historical daily climatological data
    # ─────────────────────────────────────────

    async def get_historical_observations(
        self, station_id: str, start: date, end: date
    ) -> List[Dict]:
        """
        GET /api/valores/climatologicos/diarios/datos/
                fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}

        AEMET limits date windows to 31 days; we chunk automatically.
        Date format required: YYYY-MM-DDTHH:MM:SSUTC
        """
        all_records: List[Dict] = []
        current = start

        while current <= end:
            window_end = min(current + timedelta(days=30), end)
            start_str = current.strftime("%Y-%m-%dT00:00:00UTC")
            end_str   = window_end.strftime("%Y-%m-%dT23:59:59UTC")

            endpoint = (
                f"/valores/climatologicos/diarios/datos/"
                f"fechaini/{start_str}/fechafin/{end_str}/estacion/{station_id}/"
            )
            try:
                data_url = await self._get_data_url(endpoint)
                if data_url:
                    records = await self._fetch_data(data_url)
                    if records:
                        all_records.extend(records)
                # AEMET rate-limit: respect ~1 req/s
                await asyncio.sleep(1.2)
            except Exception as e:
                logger.error(
                    f"AEMET historical error — station={station_id} "
                    f"window={current}→{window_end}: {e}"
                )

            current = window_end + timedelta(days=1)

        return all_records

    # ─────────────────────────────────────────
    # Forecasts
    # ─────────────────────────────────────────

    async def get_forecast_municipality(self, municipality_code: str) -> Optional[Dict]:
        """
        GET /api/prediccion/especifica/municipio/horaria/{municipio}
        Hourly forecast for a municipality (5-digit INE code).
        """
        endpoint = f"/prediccion/especifica/municipio/horaria/{municipality_code}/"
        data_url = await self._get_data_url(endpoint)
        if not data_url:
            return None
        return await self._fetch_data(data_url)

    async def get_forecast_province(self, province_code: str = "15") -> List[Dict]:
        """
        GET /api/prediccion/provincia/manana/{provincia}
        A Coruña province code = "15".
        """
        endpoint = f"/prediccion/provincia/manana/{province_code}/"
        data_url = await self._get_data_url(endpoint)
        if not data_url:
            return []
        data = await self._fetch_data(data_url)
        return data if isinstance(data, list) else []

    # kept for backward compat
    async def get_forecast_all_acoruna(self) -> List[Dict]:
        return await self.get_forecast_province("15")

    async def get_uv_index(self) -> Optional[Dict]:
        """GET /api/prediccion/especifica/uvi/0/"""
        data_url = await self._get_data_url("/prediccion/especifica/uvi/0/")
        if not data_url:
            return None
        return await self._fetch_data(data_url)


# ─────────────────────────────────────────────────────
# Parser for daily climatological records
# (campos de /valores/climatologicos/diarios/datos/…)
# ─────────────────────────────────────────────────────

def parse_aemet_observation(raw: Dict, station_id: str) -> Optional[Dict]:
    """
    Parse a raw AEMET daily climatological record into a normalised dict.

    Key field names from the diarios endpoint:
      fecha    – YYYY-MM-DD
      tmed     – average temperature (°C, comma decimal)
      tmin     – minimum temperature
      tmax     – maximum temperature
      prec     – precipitation (mm)
      velmedia – mean wind speed (km/h)
      racha    – max wind gust (km/h)
      dir      – dominant wind direction (cardinal or numeric)
      presMax  – max pressure (hPa)
      presMin  – min pressure
      hrMedia  – mean relative humidity (%)
      hrMax    – max relative humidity
      sol      – sunshine hours
    """
    try:
        def _float(val):
            if val is None or val in ("", "Ip", "Ac", "---"):
                return None
            try:
                return float(str(val).replace(",", "."))
            except (ValueError, TypeError):
                return None

        # Support both daily (fecha) and hourly (fint) timestamp fields
        date_str = raw.get("fecha") or raw.get("fint")
        if not date_str:
            return None

        # Normalise timestamp: "YYYY-MM-DD" → midnight UTC; "...UTC" → aware dt
        date_str_norm = date_str.replace("UTC", "+00:00").replace("Z", "+00:00")
        try:
            if "T" in date_str_norm:
                observed_at = datetime.fromisoformat(date_str_norm)
            else:
                observed_at = datetime.fromisoformat(date_str_norm + "T00:00:00+00:00")
        except ValueError:
            logger.debug(f"AEMET: cannot parse date '{date_str}'")
            return None

        # Wind direction: Spanish cardinal → degrees
        wind_dir_map = {
            "N": 0,   "NNE": 22.5, "NE": 45,  "ENE": 67.5,
            "E": 90,  "ESE": 112.5,"SE": 135,  "SSE": 157.5,
            "S": 180, "SSO": 202.5,"SO": 225,  "OSO": 247.5,
            "O": 270, "ONO": 292.5,"NO": 315,  "NNO": 337.5,
            "C": 0,
        }
        wind_dir_raw = raw.get("dir") or raw.get("dv")
        if wind_dir_raw:
            wind_dir = wind_dir_map.get(
                str(wind_dir_raw).strip().upper(),
                _float(wind_dir_raw)
            )
        else:
            wind_dir = None

        # Humidity: daily endpoint may provide hrMedia or hr
        humidity = _float(raw.get("hrMedia") or raw.get("hrmed") or raw.get("hr"))

        # Pressure: use average of max/min if available
        pres_max = _float(raw.get("presMax"))
        pres_min = _float(raw.get("presMin"))
        if pres_max is not None and pres_min is not None:
            pressure = round((pres_max + pres_min) / 2, 1)
        else:
            pressure = pres_max or pres_min or _float(raw.get("pres"))

        return {
            "station_external_id": station_id,
            "observed_at":         observed_at,
            "temperature":         _float(raw.get("tmed") or raw.get("ta")),
            "temperature_min":     _float(raw.get("tmin")),
            "temperature_max":     _float(raw.get("tmax")),
            "humidity":            humidity,
            "precipitation":       _float(raw.get("prec")),
            "wind_speed":          _float(raw.get("velmedia") or raw.get("vv")),
            "wind_gust":           _float(raw.get("racha") or raw.get("vmax")),
            "wind_direction":      wind_dir,
            "pressure":            pressure,
            "visibility":          _float(raw.get("vis")),
            "cloud_cover":         _float(raw.get("nub")),
            "solar_radiation":     _float(raw.get("sol")),   # sunshine hours (proxy)
            "fog":                 False,
        }
    except Exception as e:
        logger.debug(f"Failed to parse AEMET observation: {e} — raw={raw}")
        return None
