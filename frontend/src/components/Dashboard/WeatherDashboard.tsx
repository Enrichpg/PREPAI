import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, BarChart, Bar
} from 'recharts';
import { useHistoricalStats } from '../../hooks/useWeather';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { ErrorAlert } from '../UI/ErrorAlert';
import type { ModelMetrics, DataIngestionLog } from '../../types';

const MONTHS_ES = [
  'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
  'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
];

interface Props {
  modelMetrics: ModelMetrics | null;
  ingestionLogs: DataIngestionLog[];
  lastUpdate: string | null;
}

export const WeatherDashboard: React.FC<Props> = ({ modelMetrics, ingestionLogs, lastUpdate }) => {
  const { stats, loading, error } = useHistoricalStats();

  const monthlyData = MONTHS_ES.map((name, i) => {
    const month = i + 1;
    const records = stats.filter(s => s.month === month);
    return {
      month: name,
      avg_temperature: records.length
        ? records.reduce((a, b) => a + (b.avg_temperature || 0), 0) / records.length
        : null,
      avg_precipitation: records.length
        ? records.reduce((a, b) => a + (b.avg_precipitation || 0), 0) / records.length
        : null,
      fog_pct: records.length
        ? records.reduce((a, b) => a + (b.fog_days_pct || 0), 0) / records.length
        : null,
    };
  });

  return (
    <div className="space-y-6 p-4">
      <h2 className="text-xl font-bold text-gray-800">Panel de datos</h2>

      {/* Status bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          title="Última actualización"
          value={lastUpdate ? new Date(lastUpdate).toLocaleDateString('es-ES') : 'Sin datos'}
          icon="🔄"
        />
        <StatCard
          title="Versión modelo"
          value={modelMetrics?.version || 'No entrenado'}
          icon="🤖"
        />
        {modelMetrics?.metrics && (
          <>
            <StatCard
              title="MAE modelo"
              value={`${modelMetrics.metrics.mae.toFixed(2)} pts`}
              icon="📊"
            />
            <StatCard
              title="R² modelo"
              value={modelMetrics.metrics.r2.toFixed(3)}
              icon="✅"
            />
          </>
        )}
      </div>

      {/* Historical temperature & precipitation */}
      {loading && <LoadingSpinner message="Cargando estadísticas..." />}
      {error && <ErrorAlert message={error} />}

      {!loading && stats.length > 0 && (
        <>
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Temperatura media mensual (°C)</h3>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={monthlyData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v?.toFixed(1)}°C`, 'Temperatura']} />
                <Line type="monotone" dataKey="avg_temperature" stroke="#16a34a" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Precipitación media mensual (mm)</h3>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={monthlyData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v?.toFixed(1)} mm`, 'Precipitación']} />
                <Bar dataKey="avg_precipitation" fill="#60a5fa" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Días con niebla (%)</h3>
            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={monthlyData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v?.toFixed(1)}%`, 'Niebla']} />
                <Bar dataKey="fog_pct" fill="#94a3b8" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* Ingestion logs */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Últimas ingestas de datos</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {ingestionLogs.map(log => (
            <div key={log.id} className="flex items-center justify-between text-xs bg-gray-50 rounded-lg px-3 py-2">
              <div>
                <span className={`font-medium ${log.status === 'success' ? 'text-green-700' : log.status === 'failed' ? 'text-red-600' : 'text-yellow-700'}`}>
                  {log.status === 'success' ? '✓' : log.status === 'failed' ? '✗' : '⋯'} {log.source}
                </span>
                <span className="text-gray-500 ml-2">{log.task_name}</span>
              </div>
              <div className="text-right text-gray-400">
                <div>{new Date(log.started_at).toLocaleString('es-ES')}</div>
                <div>{log.records_inserted} insertados</div>
              </div>
            </div>
          ))}
          {ingestionLogs.length === 0 && (
            <p className="text-sm text-gray-400 italic">Sin registros de ingesta</p>
          )}
        </div>
      </div>

      {/* Feature importances */}
      {modelMetrics?.metrics?.feature_importances && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Importancia de variables (modelo ML)</h3>
          <div className="space-y-1">
            {Object.entries(modelMetrics.metrics.feature_importances)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 10)
              .map(([feat, imp]) => (
                <div key={feat} className="flex items-center gap-2 text-xs">
                  <span className="w-32 text-gray-600 truncate">{feat}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(imp * 100).toFixed(1)}%` }}
                    />
                  </div>
                  <span className="text-gray-500 w-12 text-right">{(imp * 100).toFixed(1)}%</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard: React.FC<{ title: string; value: string; icon: string }> = ({ title, value, icon }) => (
  <div className="rounded-xl border border-gray-100 bg-white p-3 shadow-sm">
    <div className="text-lg mb-1">{icon}</div>
    <div className="text-xs text-gray-500">{title}</div>
    <div className="text-sm font-semibold text-gray-800 mt-0.5">{value}</div>
  </div>
);
