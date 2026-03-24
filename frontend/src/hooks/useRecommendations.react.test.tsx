import { render, screen, waitFor } from '@testing-library/react';
import { useRecommendations } from './useRecommendations';
import React from 'react';

function TestComponent({ request }: { request: any }) {
  const { recommendations, fetchRecommendations, loading, error, clear } = useRecommendations();
  React.useEffect(() => {
    fetchRecommendations(request);
  }, [request, fetchRecommendations]);
  return (
    <div>
      <div data-testid="loading">{loading ? 'loading' : 'done'}</div>
      <div data-testid="error">{error}</div>
      <div data-testid="recommendations">{JSON.stringify(recommendations)}</div>
      <button onClick={clear}>Clear</button>
    </div>
  );
}

describe('useRecommendations (React 18+)', () => {
  it('fetches recommendations', async () => {
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
        surface_type: 'mixed' as any,
        elevation_profile: 'flat' as any,
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
    jest.spyOn(require('../services/api').routesApi, 'recommendRoutes').mockResolvedValue([mockRecommendation]);
    render(<TestComponent request={{ start_lat: 1, start_lon: 2, preferred_surface: 'mixed', preferred_elevation: 'flat', date: '2024-01-01', time_start: 7, time_end: 9, max_results: 5, search_radius_km: 10 }} />);
    await waitFor(() => expect(screen.getByTestId('recommendations').textContent).toContain('Test'));
  });

  it('clears recommendations', async () => {
    render(<TestComponent request={{}} />);
    await waitFor(() => expect(screen.getByTestId('recommendations').textContent).toBe('[]'));
  });
});
