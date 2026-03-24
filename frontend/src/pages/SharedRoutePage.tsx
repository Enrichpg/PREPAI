import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { routesApi } from '../services/api';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { ErrorAlert } from '../components/UI/ErrorAlert';
import { ElevationChart } from '../components/Routes/ElevationChart';
import { surfaceLabel, elevationLabel, formatDuration } from '../utils/comfort';
import type { SavedRoute } from '../types';

export const SharedRoutePage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [savedRoute, setSavedRoute] = useState<SavedRoute | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    routesApi.getSharedRoute(token)
      .then(setSavedRoute)
      .catch((err: any) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <LoadingSpinner message="Cargando ruta compartida..." />;

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        <Link to="/" className="text-green-600 text-sm hover:underline mb-4 inline-block">
          ← Volver a PREPAI
        </Link>

        {error && <ErrorAlert message={error} />}

        {savedRoute?.route && (
          <div className="bg-white rounded-2xl shadow-md p-6 space-y-4">
            <h1 className="text-2xl font-bold text-gray-900">{savedRoute.nickname || savedRoute.route.name}</h1>
            {savedRoute.notes && <p className="text-gray-600">{savedRoute.notes}</p>}

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Distancia</p>
                <p className="font-semibold">{savedRoute.route.distance_km.toFixed(1)} km</p>
              </div>
              {savedRoute.route.estimated_duration_min && (
                <div>
                  <p className="text-gray-500">Tiempo estimado</p>
                  <p className="font-semibold">{formatDuration(savedRoute.route.estimated_duration_min)}</p>
                </div>
              )}
              <div>
                <p className="text-gray-500">Superficie</p>
                <p className="font-semibold">{surfaceLabel(savedRoute.route.surface_type)}</p>
              </div>
              <div>
                <p className="text-gray-500">Desnivel</p>
                <p className="font-semibold">{elevationLabel(savedRoute.route.elevation_profile)}</p>
              </div>
              {savedRoute.route.elevation_gain !== null && (
                <div>
                  <p className="text-gray-500">Desnivel positivo</p>
                  <p className="font-semibold">{savedRoute.route.elevation_gain?.toFixed(0)}m</p>
                </div>
              )}
              {savedRoute.route.municipality && (
                <div>
                  <p className="text-gray-500">Municipio</p>
                  <p className="font-semibold">{savedRoute.route.municipality}</p>
                </div>
              )}
            </div>

            {savedRoute.route.elevation_data && savedRoute.route.elevation_data.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-gray-600 mb-2">Perfil de elevación</p>
                <ElevationChart data={savedRoute.route.elevation_data} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
