export interface WeatherStation {
  id: number;
  station_id: string;
  name: string;
  municipality: string | null;
  province: string;
  source: 'aemet' | 'meteogalicia';
  altitude: number | null;
  latitude: number | null;
  longitude: number | null;
  is_active: boolean;
  zone_id: number | null;
}

export interface WeatherObservation {
  id: number;
  station_id: number;
  observed_at: string;
  temperature: number | null;
  feels_like: number | null;
  humidity: number | null;
  precipitation: number | null;
  wind_speed: number | null;
  wind_gust: number | null;
  wind_direction: number | null;
  pressure: number | null;
  visibility: number | null;
  cloud_cover: number | null;
  uv_index: number | null;
  fog: boolean;
  weather_description: string | null;
}

export interface HourlyComfortForecast {
  hour: number;
  datetime: string;
  comfort_score: number;
  temperature: number | null;
  precipitation: number | null;
  wind_speed: number | null;
  humidity: number | null;
  weather_description: string | null;
  warnings: string[];
}

export interface ZoneForecastSummary {
  zone_id: number;
  zone_name: string;
  date: string;
  hourly: HourlyComfortForecast[];
  best_window_start: number | null;
  best_window_end: number | null;
  daily_max_comfort: number;
}

export type SurfaceType = 'asphalt' | 'trail' | 'mixed' | 'gravel' | 'track';
export type ElevationProfile = 'flat' | 'moderate' | 'hilly';

export interface RunningRoute {
  id: number;
  osm_id: string | null;
  name: string;
  description: string | null;
  distance_km: number;
  elevation_gain: number | null;
  elevation_loss: number | null;
  elevation_min: number | null;
  elevation_max: number | null;
  estimated_duration_min: number | null;
  surface_type: SurfaceType;
  elevation_profile: ElevationProfile;
  difficulty: string | null;
  is_loop: boolean;
  municipality: string | null;
  zone_id: number | null;
  is_verified: boolean;
  elevation_data: Array<{ distance: number; altitude: number }> | null;
  tags: Record<string, string> | null;
  geojson: GeoJSONFeature | null;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: 'LineString';
    coordinates: [number, number][];
  };
  properties: Record<string, unknown>;
}

export interface WeatherWarning {
  type: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
}

export interface RouteRecommendationOut {
  route: RunningRoute;
  comfort_score: number;
  match_score: number;
  overall_score: number;
  rank: number;
  weather_summary: WeatherSummary;
  warnings: WeatherWarning[];
  hourly_comfort: HourlyComfortForecast[];
}

export interface WeatherSummary {
  temp_min: number | null;
  temp_max: number | null;
  temp_avg: number | null;
  precipitation_total: number;
  max_wind_speed: number;
  max_wind_gust: number;
  avg_humidity: number;
  has_fog: boolean;
  max_uv: number;
}

export interface RecommendationRequest {
  target_distance_km?: number;
  target_duration_min?: number;
  preferred_surface: SurfaceType;
  preferred_elevation: ElevationProfile;
  start_lat: number;
  start_lon: number;
  date: string;
  time_start: number;
  time_end: number;
  max_results: number;
  search_radius_km: number;
}

export interface Zone {
  id: number;
  name: string;
  municipality: string;
  comarca: string | null;
  province: string;
  altitude_mean: number | null;
  centroid_lat: number | null;
  centroid_lon: number | null;
}

export interface HeatmapPoint {
  zone_id: number;
  zone_name: string;
  lat: number | null;
  lon: number | null;
  avg_comfort: number | null;
  max_comfort: number | null;
}

export interface HistoricalStats {
  zone_id: number;
  zone_name: string;
  month: number;
  avg_temperature: number | null;
  avg_precipitation: number | null;
  avg_humidity: number | null;
  avg_wind_speed: number | null;
  fog_days_pct: number | null;
}

export interface ModelMetrics {
  version: string;
  metrics: {
    mae: number;
    rmse: number;
    r2: number;
    training_samples: number;
    validation_samples: number;
    feature_importances: Record<string, number>;
  };
}

export interface DataIngestionLog {
  id: number;
  source: string;
  task_name: string | null;
  started_at: string;
  finished_at: string | null;
  status: string;
  records_fetched: number;
  records_inserted: number;
  records_updated: number;
  error_message: string | null;
}

export interface SavedRoute {
  id: number;
  route_id: number;
  session_id: string;
  nickname: string | null;
  notes: string | null;
  share_token: string;
  created_at: string;
  route: RunningRoute | null;
}
