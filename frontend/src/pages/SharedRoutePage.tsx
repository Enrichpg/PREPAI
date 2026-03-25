import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { routesApi } from '../services/api';
import { MapView } from '../components/Map/MapView';
import { RouteCard } from '../components/Routes/RouteCard';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { ErrorAlert } from '../components/UI/ErrorAlert';
import { Icon } from '../components/UI/Icon';
import type { RouteRecommendationOut } from '../types';

export const SharedRoutePage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [recommendation, setRecommendation] = useState<RouteRecommendationOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    routesApi.getSharedRoute(token)
      .then(saved => {
        if (saved.route) {
          // Create a mock recommendation as SavedRoute doesn't include comfort scores
          const mockRec: RouteRecommendationOut = {
            route: saved.route,
            comfort_score: 85, // Default placeholder
            match_score: 90,
            overall_score: 88,
            rank: 1,
            weather_summary: {
              temp_min: 12, temp_max: 18, temp_avg: 15,
              precipitation_total: 0, max_wind_speed: 10,
              max_wind_gust: 15, avg_humidity: 60, has_fog: false, max_uv: 3
            },
            warnings: [],
            hourly_comfort: []
          };
          setRecommendation(mockRec);
        } else {
          setError('La ruta no tiene datos geográficos válidos.');
        }
      })
      .catch(() => setError('No se pudo encontrar la ruta compartida o el enlace ha caducado.'))
      .finally(() => setLoading(false));
  }, [token]);


  if (loading) return (
    <div className="h-screen flex items-center justify-center bg-surface-950">
      <LoadingSpinner message="Obteniendo ruta compartida..." size="lg" />
    </div>
  );

  return (
    <div className="flex h-screen flex-col bg-surface-950 overflow-hidden">
      {/* ── Header ─────────────────────────────────────────── */}
      <header
        className="flex items-center justify-between px-5 py-3 z-20 flex-shrink-0"
        style={{
          background: 'rgba(6,6,9,0.92)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
          <div className="flex items-center gap-2">
            <Icon name="run" size={24} style={{ color: '#ff5722' }} />
            <h1
              className="font-display tracking-widest text-white uppercase text-xl"
              style={{ fontFamily: '"Bebas Neue", sans-serif', letterSpacing: '0.1em' }}
            >
              PREP<span style={{ color: '#ff5722' }}>AI</span>
            </h1>
          </div>
        </div>
        <button
          onClick={() => navigate('/')}
          className="btn-brand !w-auto py-1.5 px-4 text-xs flex items-center gap-2"
        >
          <Icon name="search" size={13} />
          CREAR MI PROPIA RUTA
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-full md:w-96 flex flex-col z-10 glass-panel border-r border-white/5 animate-fade-up">
          <div className="p-4 flex-1 overflow-y-auto space-y-4">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-brand-500 uppercase tracking-[0.2em]">Ruta Compartida</span>
              <h2 className="text-xl font-bold text-white leading-tight">Preparada para ti</h2>
            </div>

            {error ? (
              <ErrorAlert message={error} />
            ) : recommendation ? (
              <RouteCard
                recommendation={recommendation}
                onSelect={() => {}}
                onSave={() => {}}
                isSelected={true}
              />
            ) : null}

            <div className="pt-6 border-t border-white/5">
              <p className="text-[11px] text-muted leading-relaxed">
                Esta ruta ha sido seleccionada basándose en las condiciones climáticas de la zona y un perfil de entrenamiento optimizado.
              </p>
            </div>
          </div>
        </aside>

        {/* Map */}
        <main className="hidden md:flex flex-1 relative">
          {recommendation && (
            <MapView
              recommendations={[recommendation]}
              selectedRec={recommendation}
              onSelectRec={() => {}}
              userPosition={null}
              showHeatmap={false}
              heatmap={[]}
            />
          )}
        </main>
      </div>
    </div>
  );
};
