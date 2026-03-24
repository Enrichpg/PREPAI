import { useState, useCallback } from 'react';
import { routesApi } from '../services/api';
import type { RouteRecommendationOut, RecommendationRequest } from '../types';

export function useRecommendations() {
  const [recommendations, setRecommendations] = useState<RouteRecommendationOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async (request: RecommendationRequest) => {
    setLoading(true);
    setError(null);
    try {
      const data = await routesApi.recommendRoutes(request);
      setRecommendations(data);
      // Si el array está vacío, no es error, solo no hay rutas
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al obtener recomendaciones');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setRecommendations([]);
    setError(null);
  }, []);

  return { recommendations, loading, error, fetchRecommendations, clear };
}
