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
import { useRecommendations } from './useRecommendations';
import '@testing-library/jest-dom';

describe('useRecommendations', () => {
  it('fetches recommendations', async () => {
    // Mock mínimo válido para RouteRecommendationOut
    const mockRecommendation = {
      route: {
        id: 1,
        osm_id: null,
        name: 'Test',
        description: null,
        distance_km: 10,
        elevation_gain: null,
        elevation_loss: null,
        elevation_min: null,
        elevation_max: null,
        estimated_duration_min: null,
        surface_type: 'mixed' as import('../types').SurfaceType,
        elevation_profile: 'flat' as import('../types').ElevationProfile,
        difficulty: null,
        is_loop: false,
        municipality: null,
        zone_id: null,
        is_verified: false,
        elevation_data: null,
        tags: null,
        geojson: null
      },
      comfort_score: 0.9,
      match_score: 0.8,
      overall_score: 0.85,
      rank: 1,
      weather_summary: {
        temp_min: null,
        temp_max: null,
        temp_avg: null,
        precipitation_total: 0,
        max_wind_speed: 0,
        max_wind_gust: 0,
        avg_humidity: 0,
        has_fog: false,
        max_uv: 0
      },
      warnings: [],
      hourly_comfort: []
    };
    jest.spyOn(api.routesApi, 'recommendRoutes').mockResolvedValue([mockRecommendation]);
    const { result } = renderHook(() => useRecommendations());
    await act(async () => {
      await result.current.fetchRecommendations({ start_lat: 1, start_lon: 2, preferred_surface: 'mixed', preferred_elevation: 'flat', date: '2024-01-01', time_start: 7, time_end: 9, max_results: 5, search_radius_km: 10 });
    });
    expect(result.current.recommendations).toEqual([mockRecommendation]);
  });

  it('clears recommendations', () => {
    const { result } = renderHook(() => useRecommendations());
    act(() => {
      result.current.clear();
    });
    expect(result.current.recommendations).toEqual([]);
  });
});
