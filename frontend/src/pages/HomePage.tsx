import React, { useState, useEffect, useCallback } from 'react';
import { MapView } from '../components/Map/MapView';
import { SearchForm } from '../components/Filters/SearchForm';
import { RouteCard } from '../components/Routes/RouteCard';
import { WeatherDashboard } from '../components/Dashboard/WeatherDashboard';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { ErrorAlert } from '../components/UI/ErrorAlert';
import { Icon } from '../components/UI/Icon';
import { useRecommendations } from '../hooks/useRecommendations';
import { useHeatmap } from '../hooks/useWeather';
import { weatherApi, mlApi, routesApi } from '../services/api';
import { getSessionId } from '../utils/session';
import type { RouteRecommendationOut, ModelMetrics, DataIngestionLog } from '../types';
import { format } from 'date-fns';

type Tab = 'search' | 'dashboard';

/* ── Inline SVG runner logo ─────────────────────────────────── */
const RunnerLogo: React.FC = () => (
  <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
    {/* Head */}
    <circle cx="20" cy="5" r="3" fill="#ff5722" />
    {/* Body */}
    <path d="M20 8 L17 14 L13 18" stroke="#ff5722" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    {/* Arms */}
    <path d="M17 12 L22 10 L26 12" stroke="#ff5722" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    {/* Back leg */}
    <path d="M13 18 L10 23 L7 27" stroke="#ff5722" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    {/* Front leg */}
    <path d="M17 14 L20 19 L24 22" stroke="#00e5a0" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    {/* Ground line */}
    <line x1="5" y1="27" x2="28" y2="27" stroke="rgba(255,87,34,0.3)" strokeWidth="1.5" strokeLinecap="round"/>
  </svg>
);

export const HomePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('search');
  const [selectedRec, setSelectedRec] = useState<RouteRecommendationOut | null>(null);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapDate] = useState<string>(format(new Date(), 'yyyy-MM-dd'));
  const [userPosition, setUserPosition] = useState<[number, number] | null>(null);
  const [modelMetrics, setModelMetrics] = useState<ModelMetrics | null>(null);
  const [ingestionLogs, setIngestionLogs] = useState<DataIngestionLog[]>([]);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [searchedPosition, setSearchedPosition] = useState<[number, number] | null>(null);

  const { recommendations, loading, error, fetchRecommendations, clear } = useRecommendations();
  const { heatmap } = useHeatmap(heatmapDate);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => setUserPosition([pos.coords.latitude, pos.coords.longitude]),
        () => {}
      );
    }
  }, []);

  useEffect(() => {
    mlApi.getModelMetrics()
      .then((m: ModelMetrics) => setModelMetrics(m))
      .catch(() => {});
    weatherApi.getIngestionLogs(10)
      .then((logs: DataIngestionLog[]) => {
        setIngestionLogs(logs);
        const last = logs.find((l: DataIngestionLog) => l.status === 'success' && l.finished_at);
        if (last?.finished_at) setLastUpdate(last.finished_at);
      })
      .catch(() => {});
  }, []);

  const handleSaveRoute = useCallback(async (routeId: number) => {
    const sessionId = getSessionId();
    try {
      const saved = await routesApi.saveRoute(routeId, sessionId);
      setSaveMessage(`Ruta guardada · /shared/${saved.share_token}`);
      setTimeout(() => setSaveMessage(null), 4000);
    } catch {
      setSaveMessage('Error al guardar la ruta');
      setTimeout(() => setSaveMessage(null), 3000);
    }
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden" style={{ background: 'var(--surface-bg)' }}>

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
        <div className="flex items-center gap-3">
          <RunnerLogo />
          <div>
            <h1
              className="font-display leading-none tracking-wider"
              style={{ fontSize: '1.35rem', color: '#f0f0f5', fontFamily: '"Bebas Neue", sans-serif', letterSpacing: '0.12em' }}
            >
              PREP<span style={{ color: '#ff5722' }}>AI</span>
            </h1>
            <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.1em', fontWeight: 500 }}>
              RUTAS DE RUNNING · A CORUÑA
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowHeatmap(h => !h)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full transition-all"
          style={{
            background: showHeatmap ? 'rgba(255,87,34,0.15)' : 'rgba(255,255,255,0.05)',
            border: `1px solid ${showHeatmap ? 'rgba(255,87,34,0.5)' : 'rgba(255,255,255,0.1)'}`,
            color: showHeatmap ? '#ff7035' : 'var(--text-secondary)',
            fontSize: '0.75rem',
            fontWeight: 600,
            letterSpacing: '0.05em',
          }}
        >
          <Icon name="heatmap" size={14} />
          MAPA CALOR
        </button>
      </header>

      {/* ── Toast notification ─────────────────────────────── */}
      {saveMessage && (
        <div
          className="absolute top-16 right-4 z-50 text-sm rounded-xl px-4 py-3 shadow-lg animate-fade-up flex items-center gap-2"
          style={{
            background: 'linear-gradient(135deg, #10101e, #161628)',
            border: '1px solid rgba(0,229,160,0.4)',
            color: '#00e5a0',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
          }}
        >
          <Icon name="check" size={14} />
          {saveMessage}
        </div>
      )}

      {/* ── Main layout ────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* Sidebar */}
        <aside
          className="w-full md:w-96 flex flex-col z-10 overflow-hidden glass-panel flex-shrink-0"
          style={{ borderRight: '1px solid rgba(255,255,255,0.06)', borderTop: 'none' }}
        >
          {/* Tabs */}
          <div
            className="flex flex-shrink-0"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}
          >
            {(['search', 'dashboard'] as Tab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`tab-item${activeTab === tab ? ' active' : ''}`}
              >
                <span className="flex items-center justify-center gap-1.5">
                  <Icon name={tab === 'search' ? 'search' : 'chart'} size={13} />
                  {tab === 'search' ? 'Buscar' : 'Datos'}
                </span>
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
            {activeTab === 'search' && (
              <div className="p-4 space-y-4 animate-fade-up">
                <SearchForm
                  onSearch={fetchRecommendations}
                  loading={loading}
                  userPosition={userPosition}
                  setSearchedPosition={setSearchedPosition}
                />

                {error && <ErrorAlert message={error} onDismiss={clear} />}
                {loading && <LoadingSpinner message="Calculando mejores rutas..." />}

                {!loading && recommendations.length > 0 && (
                  <div className="space-y-3 animate-fade-up">
                    <div className="flex items-center justify-between">
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.1em' }}>
                        {recommendations.length} RUTAS RECOMENDADAS
                      </span>
                      <button
                        onClick={clear}
                        style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}
                        className="hover:text-white transition-colors flex items-center gap-1"
                      >
                        <Icon name="close" size={11} /> Limpiar
                      </button>
                    </div>
                    {recommendations.map(rec => (
                      <RouteCard
                        key={rec.route.id}
                        recommendation={rec}
                        onSelect={setSelectedRec}
                        onSave={handleSaveRoute}
                        isSelected={selectedRec?.route.id === rec.route.id}
                      />
                    ))}
                  </div>
                )}

                {!loading && !error && recommendations.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 gap-3" style={{ color: 'var(--text-muted)' }}>
                    {/* Abstract path/route graphic */}
                    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" aria-hidden="true">
                      <circle cx="32" cy="32" r="30" stroke="rgba(255,87,34,0.12)" strokeWidth="1"/>
                      <circle cx="32" cy="32" r="22" stroke="rgba(255,87,34,0.08)" strokeWidth="1"/>
                      <path d="M12 44 C20 36 24 28 32 28 C40 28 44 36 52 28" stroke="rgba(255,87,34,0.35)" strokeWidth="2" strokeLinecap="round" fill="none"/>
                      <circle cx="12" cy="44" r="3" fill="rgba(255,87,34,0.5)"/>
                      <circle cx="52" cy="28" r="3" fill="rgba(0,229,160,0.5)"/>
                    </svg>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      Define tus preferencias
                    </p>
                    <p style={{ fontSize: '0.7rem', textAlign: 'center', lineHeight: 1.5 }}>
                      El sistema analizará el clima y te<br/>recomendará las rutas óptimas
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'dashboard' && (
              <WeatherDashboard
                modelMetrics={modelMetrics}
                ingestionLogs={ingestionLogs}
                lastUpdate={lastUpdate}
              />
            )}
          </div>
        </aside>

        {/* Map area */}
        <main className="hidden md:flex flex-1 relative">
          <MapView
            recommendations={recommendations}
            heatmap={heatmap}
            selectedRec={selectedRec}
            onSelectRec={setSelectedRec}
            userPosition={userPosition}
            showHeatmap={showHeatmap}
            searchedPosition={searchedPosition}
          />
        </main>
      </div>
    </div>
  );
};


