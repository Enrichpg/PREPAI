"""
MeteoGalicia API v4 client.
Docs: https://www.meteogalicia.gal/web/RSS/rssIndex.action
API: https://servizos.meteogalicia.gal/apiv4
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

from app.core.config import settings


# MeteoGalicia station IDs for A Coruña province (idEstacion)
METEOGALICIA_ACORUNA_STATIONS = [
    10045, 10046, 10061, 10062, 10101, 10102, 10103,
    10104, 10140, 10141, 10142, 10143, 10157, 10158,
    10159, 10160, 10177, 10178, 10200, 10201, 10220,
    10221, 10222, 10240, 10241, 10242, 10260, 10261,
]

# A Coruña concellos (municipality codes for MeteoGalicia)
ACORUNA_CONCELLOS = [
    15001, 15002, 15003, 15004, 15005, 15006, 15007, 15008,
    15009, 15010, 15011, 15012, 15013, 15014, 15015, 15016,
    15017, 15018, 15019, 15020, 15021, 15022, 15023, 15024,
    15025, 15026, 15027, 15028, 15029, 15030, 15031, 15032,
]


class MeteoGaliciaClient:
    BASE_URL = settings.METEOGALICIA_BASE_URL

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.METEOGALICIA_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={"Accept": "application/json"},
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
    async def _get(self, endpoint: str, params: Dict = None) -> Optional[Any]:
        url = f"{self.BASE_URL}{endpoint}"
        resp = await self._client.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()

    async def get_stations(self) -> List[Dict]:
        """List all MeteoGalicia automatic weather stations."""
        data = await self._get("/getEstacions", {"request": "getEstacions", "idEdo": "1"})
        if not data:
            return []
        stations = data.get("features") or data.get("listEst") or []
        # Filter to A Coruña province
        result = []
        for s in stations:
            props = s.get("properties") or s
            # MeteoGalicia province code for A Coruña is 15
            if str(props.get("idProvincia", "")).startswith("15") or \
               "coruña" in str(props.get("provincia", "")).lower() or \
               "coruña" in str(props.get("concello", "")).lower():

    async def get_recent_observations(self, station_id: int) -> Optional[Dict]:
        """Fetch last 24h observations for a station."""
        return await self._get(
            "/getUltimosDatos",
            {"request": "getUltimosDatos", "idEstacion": station_id},
        )

    async def get_lightning(self) -> Optional[Dict]:
        """Fetch recent lightning activity (useful for storm warnings)."""
        return await self._get("/getRelampagos", {"request": "getRelampagos"})


def parse_meteogalicia_observation(raw: Dict, station_id: int) -> Optional[Dict]:
    """Parse a raw MeteoGalicia record into a normalised dict."""
    try:
        def _float(val):
            if val is None or val in ("", "-9999", -9999, -9999.0, "null"):
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        # MeteoGalicia datetime fields vary by endpoint
        ts = raw.get("instantedt") or raw.get("dataHora") or raw.get("data")
        if not ts:
            return None
        if isinstance(ts, (int, float)):
            observed_at = datetime.utcfromtimestamp(ts / 1000)
        else:
            observed_at = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))

        # Detect fog from visibility < 1km
        visibility = _float(raw.get("visibilidade") or raw.get("vis"))
        fog = (visibility is not None and visibility < 1.0)

        return {
            "station_external_id": str(station_id),
            "observed_at": observed_at,
            "temperature": _float(raw.get("temperatura") or raw.get("temp") or raw.get("ta")),
            "temperature_min": _float(raw.get("tmin")),
            "temperature_max": _float(raw.get("tmax")),
            "humidity": _float(raw.get("humedadeRelativa") or raw.get("hr")),
            "precipitation": _float(raw.get("precipitacion") or raw.get("prec")),
            "wind_speed": _float(raw.get("velocidadeVento") or raw.get("vv")),
            "wind_gust": _float(raw.get("rachaMaxVento") or raw.get("vmax")),
            "wind_direction": _float(raw.get("direccionVento") or raw.get("dv")),
            "pressure": _float(raw.get("presionAtmosfera") or raw.get("pres")),
            "visibility": visibility,
            "solar_radiation": _float(raw.get("radiacioSolar") or raw.get("inso")),
            "fog": fog,
        }
    except Exception as e:
        logger.debug(f"Failed to parse MeteoGalicia observation: {e} — raw={raw}")
        return None
