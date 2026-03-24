import axios, { AxiosResponse, AxiosRequestConfig } from 'axios';
import type {
  WeatherStation, ZoneForecastSummary, HeatmapPoint,
  HistoricalStats, RunningRoute, RouteRecommendationOut,
  RecommendationRequest, Zone, ModelMetrics, DataIngestionLog, SavedRoute
} from '../types';
// ...existing code...

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config: AxiosRequestConfig) => config,
  (error: any) => Promise.reject(error)
);

// Response interceptor for error normalisation
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: any) => {
    const message = error.response?.data?.detail || error.message || 'Error desconocido';
    return Promise.reject(new Error(message));
  }
);
// ...existing code...

// ── Weather ──────────────────────────────────────────────────────────────────

export const weatherApi = {
  getStations: () =>
    api.get<WeatherStation[]>('/weather/stations').then((r: AxiosResponse<WeatherStation[]>) => r.data),

  getZoneForecast: (zoneId: number, date?: string) =>
    api.get<ZoneForecastSummary>(`/weather/forecasts/${zoneId}`, {
      params: date ? { target_date: date } : {}
    }).then((r: AxiosResponse<ZoneForecastSummary>) => r.data),

  getHeatmap: (date?: string, hour?: number) =>
    api.get<HeatmapPoint[]>('/weather/heatmap', {
      params: { target_date: date, hour }
    }).then((r: AxiosResponse<HeatmapPoint[]>) => r.data),

  getHistoricalStats: (zoneId?: number) =>
    api.get<HistoricalStats[]>('/weather/historical/stats', {
      params: zoneId ? { zone_id: zoneId } : {}
    }).then((r: AxiosResponse<HistoricalStats[]>) => r.data),

  getIngestionLogs: (limit = 20) =>
    api.get<DataIngestionLog[]>('/weather/ingestion/logs', { params: { limit } })
      .then((r: AxiosResponse<DataIngestionLog[]>) => r.data),

  triggerIngestion: () =>
    api.post('/weather/ingestion/trigger').then((r: AxiosResponse<any>) => r.data),

  triggerHistoricalIngestion: (years = 10) =>
    api.post('/weather/ingestion/historical', null, { params: { years } }).then((r: AxiosResponse<any>) => r.data),
};

// ── Routes ────────────────────────────────────────────────────────────────────

export const routesApi = {
  listRoutes: (params?: {
    surface?: string;
    elevation?: string;
    min_distance?: number;
    max_distance?: number;
    municipality?: string;
    limit?: number;
    offset?: number;
  }) =>
    api.get<RunningRoute[]>('/routes/', { params }).then((r: AxiosResponse<RunningRoute[]>) => r.data),

  getRoute: (id: number) =>
    api.get<RunningRoute>(`/routes/${id}`).then((r: AxiosResponse<RunningRoute>) => r.data),

  recommendRoutes: (request: RecommendationRequest) =>
    api.post<RouteRecommendationOut[]>('/routes/recommend', request).then((r: AxiosResponse<RouteRecommendationOut[]>) => r.data),

  getRoutesNear: (lat: number, lon: number, radiusKm = 10, limit = 20) =>
    api.get<RunningRoute[]>('/routes/near', {
      params: { lat, lon, radius_km: radiusKm, limit }
    }).then((r: AxiosResponse<RunningRoute[]>) => r.data),

  saveRoute: (routeId: number, sessionId: string, nickname?: string, notes?: string) =>
    api.post<SavedRoute>('/routes/saved', {
      route_id: routeId, session_id: sessionId, nickname, notes
    }).then((r: AxiosResponse<SavedRoute>) => r.data),

  getSavedRoutes: (sessionId: string) =>
    api.get<SavedRoute[]>(`/routes/saved/${sessionId}`).then((r: AxiosResponse<SavedRoute[]>) => r.data),

  getSharedRoute: (shareToken: string) =>
    api.get<SavedRoute>(`/routes/shared/${shareToken}`).then((r: AxiosResponse<SavedRoute>) => r.data),

  importOsm: () =>
    api.post('/routes/import/osm').then((r: AxiosResponse<any>) => r.data),
};

// ── ML ────────────────────────────────────────────────────────────────────────

export const mlApi = {
  getModelMetrics: () =>
    api.get<ModelMetrics>('/ml/model/metrics').then((r: AxiosResponse<ModelMetrics>) => r.data),

  triggerTraining: () =>
    api.post('/ml/model/train').then((r: AxiosResponse<any>) => r.data),
};

// ── Zones ─────────────────────────────────────────────────────────────────────

export const zonesApi = {
  listZones: () =>
    api.get<Zone[]>('/zones/').then((r: AxiosResponse<Zone[]>) => r.data),

  getZone: (id: number) =>
    api.get<Zone>(`/zones/${id}`).then((r: AxiosResponse<Zone>) => r.data),
};

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    api.get('/health').then((r: AxiosResponse<any>) => r.data),
  status: () =>
    api.get('/status').then((r: AxiosResponse<any>) => r.data),
};

export default api;
