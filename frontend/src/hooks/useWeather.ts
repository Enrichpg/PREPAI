import { useState, useEffect } from 'react';
import { weatherApi } from '../services/api';
import type { ZoneForecastSummary, HeatmapPoint, HistoricalStats } from '../types';

export function useZoneForecast(zoneId: number | null, date?: string) {
  const [forecast, setForecast] = useState<ZoneForecastSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!zoneId) return;
    setLoading(true);
    weatherApi.getZoneForecast(zoneId, date)
      .then(setForecast)
      .catch((err: any) => setError(err.message))
      .finally(() => setLoading(false));
  }, [zoneId, date]);

  return { forecast, loading, error };
}

export function useHeatmap(date?: string, hour?: number) {
  const [heatmap, setHeatmap] = useState<HeatmapPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    weatherApi.getHeatmap(date, hour)
      .then(setHeatmap)
      .catch((err: any) => setError(err.message))
      .finally(() => setLoading(false));
  }, [date, hour]);

  return { heatmap, loading, error };
}

export function useHistoricalStats(zoneId?: number) {
  const [stats, setStats] = useState<HistoricalStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    weatherApi.getHistoricalStats(zoneId)
      .then(setStats)
      .catch((err: any) => setError(err.message))
      .finally(() => setLoading(false));
  }, [zoneId]);

  return { stats, loading, error };
}
