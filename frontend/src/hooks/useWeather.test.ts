// Mock explícito de axios.create para tests
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() }
    }
  };
  return {
    create: () => mockAxiosInstance,
  };
});
// jest will use __mocks__/axios.js automatically


jest.mock('axios');
import { renderHook, act } from '@testing-library/react-hooks';
import * as api from '../services/api';
import { useZoneForecast, useHeatmap, useHistoricalStats } from './useWeather';
import '@testing-library/jest-dom';


describe('useZoneForecast', () => {
  it('fetches forecast data', async () => {
    // Mock mínimo válido para ZoneForecastSummary
    const mockForecast = {
      zone_id: 1,
      zone_name: 'Zona Test',
      date: '2024-01-01',
      hourly: [],
      best_window_start: null,
      best_window_end: null,
      daily_max_comfort: 0
    };
    jest.spyOn(api.weatherApi, 'getZoneForecast').mockResolvedValue(mockForecast);
    const { result, waitForNextUpdate } = renderHook(() => useZoneForecast(1));
    await waitForNextUpdate();
    expect(result.current.forecast).toEqual(mockForecast);
  });
});


describe('useHeatmap', () => {
  it('fetches heatmap data', async () => {
    // Mock mínimo válido para HeatmapPoint
    const mockHeatmap = [{ zone_id: 1, zone_name: 'Zona Test', avg_comfort: 0.8, max_comfort: 1, lat: 1, lon: 2 }];
    jest.spyOn(api.weatherApi, 'getHeatmap').mockResolvedValue(mockHeatmap);
    const { result, waitForNextUpdate } = renderHook(() => useHeatmap());
    await waitForNextUpdate();
    expect(result.current.heatmap).toEqual(mockHeatmap);
  });
});


describe('useHistoricalStats', () => {
  it('fetches stats data', async () => {
    // Mock mínimo válido para HistoricalStats
    const mockStats = [{ zone_id: 1, zone_name: 'Zona Test', month: 1, avg_temperature: 15, avg_precipitation: 0, avg_humidity: 80, avg_wind_speed: 10, fog_days_pct: 0, avg_comfort_score: 0.7, best_hours: [] }];
    jest.spyOn(api.weatherApi, 'getHistoricalStats').mockResolvedValue(mockStats);
    const { result, waitForNextUpdate } = renderHook(() => useHistoricalStats());
    await waitForNextUpdate();
    expect(result.current.stats).toEqual(mockStats);
  });
});
