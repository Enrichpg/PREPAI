import React, { useState, useEffect, useCallback } from 'react';
import { MapView } from '../components/Map/MapView';
import { SearchForm } from '../components/Filters/SearchForm';
import { RouteCard } from '../components/Routes/RouteCard';
import { WeatherDashboard } from '../components/Dashboard/WeatherDashboard';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { ErrorAlert } from '../components/UI/ErrorAlert';
import { useRecommendations } from '../hooks/useRecommendations';
import { useHeatmap } from '../hooks/useWeather';
import { weatherApi, mlApi, routesApi } from '../services/api';
import { getSessionId } from '../utils/session';
import type { RouteRecommendationOut, ModelMetrics, DataIngestionLog } from '../types';
import { format } from 'date-fns';

type Tab = 'search' | 'dashboard' | 'saved';

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

  // Geolocation
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => setUserPosition([pos.coords.latitude, pos.coords.longitude]),
        () => {} // silent fail — default to A Coruña
      );
    }
  }, []);

  // Load dashboard data
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
      setSaveMessage(`Ruta guardada. Comparte: /shared/${saved.share_token}`);
      setTimeout(() => setSaveMessage(null), 4000);
    } catch {
      setSaveMessage('Error al guardar la ruta');
      setTimeout(() => setSaveMessage(null), 3000);
    }
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-gray-50">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-white shadow-sm z-10">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🏃</span>
          <div>
            <h1 className="font-bold text-gray-900 text-lg leading-tight">PREPAI</h1>
            <p className="text-xs text-gray-500">Rutas de running · A Coruña</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowHeatmap(h => !h)}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors
              ${showHeatmap ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            🌡 Mapa calor
          </button>
        </div>
      </header>

      {/* Save message toast */}
      {saveMessage && (
        <div className="absolute top-16 right-4 z-50 bg-green-700 text-white text-sm rounded-lg px-4 py-2 shadow-lg">
          {saveMessage}
        </div>
      )}

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-full md:w-96 flex flex-col bg-white shadow-md z-10 overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-gray-200">
            {(['search', 'dashboard'] as Tab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex-1 py-3 text-sm font-medium transition-colors
                  ${activeTab === tab
                    ? 'border-b-2 border-green-600 text-green-700'
                    : 'text-gray-500 hover:text-gray-700'}`}
              >
                {tab === 'search' ? '🔍 Buscar' : '📊 Datos'}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'search' && (
              <div className="p-4 space-y-4">
                <SearchForm
                  onSearch={fetchRecommendations}
                  loading={loading}
                  userPosition={userPosition}
                  setSearchedPosition={setSearchedPosition}
                />

                {error && <ErrorAlert message={error} onDismiss={clear} />}

                {loading && <LoadingSpinner message="Calculando mejores rutas..." />}

                {!loading && recommendations.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-700 text-sm">
                        {recommendations.length} rutas recomendadas
                      </h3>
                      <button onClick={clear} className="text-xs text-gray-400 hover:text-gray-600">
                        Limpiar
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
                  <div className="text-center py-8 text-gray-400 text-sm">
                    <p className="text-3xl mb-2">🗺</p>
                    <p>Usa el formulario para buscar rutas</p>
                    <p className="text-xs mt-1">adaptadas al clima y tus preferencias</p>
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

        {/* Map — hidden on mobile, full width on desktop */}
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
