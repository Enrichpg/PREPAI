import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar, Cell
} from 'recharts';
import { useHistoricalStats } from '../../hooks/useWeather';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { ErrorAlert } from '../UI/ErrorAlert';
import { Icon } from '../UI/Icon';
import type { ModelMetrics, DataIngestionLog } from '../../types';

const MONTHS_ES = [
  'ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
  'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'
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
    <div className="space-y-8 p-5 animate-fade-up pb-12">
      <div className="flex items-center gap-2">
        <Icon name="chart" size={18} style={{ color: '#ff5722' }} />
        <h2 className="text-sm font-display tracking-widest text-[#f0f0f5] uppercase font-bold" style={{ letterSpacing: '0.15em' }}>
          Análisis de Datos
        </h2>
      </div>

      {/* ── Status Metrics ─────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          title="ÚLTIMA ACTUALIZACIÓN"
          value={lastUpdate ? new Date(lastUpdate).toLocaleDateString('es-ES') : 'SIN DATOS'}
          icon="sync"
          color="#ff5722"
        />
        <StatCard
          title="MODELO"
          value={modelMetrics?.version || 'PENDIENTE'}
          icon="robot"
          color="#00e5a0"
        />
        {modelMetrics?.metrics && (
          <>
            <StatCard
              title="MAE"
              value={`${modelMetrics.metrics.mae.toFixed(2)} PTS`}
              icon="bolt"
              color="#ffc107"
            />
            <StatCard
              title="R² ACCURACY"
              value={modelMetrics.metrics.r2.toFixed(3)}
              icon="check"
              color="#00e5a0"
            />
          </>
        )}
      </div>

      {/* ── Historical Charts ─────────────────────────────── */}
      {loading && <LoadingSpinner message="Analizando historial..." />}
      {error && <ErrorAlert message={error} />}

      {!loading && stats.length > 0 && (
        <div className="space-y-8">
          <div>
            <h3 className="text-[10px] font-bold text-muted mb-4 uppercase tracking-[0.1em] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500"></span> TEMPERATURA MEDIA MENSUAL (°C)
            </h3>
            <div className="h-[180px] w-full">
              <ResponsiveContainer>
                <LineChart data={monthlyData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#10101e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '11px' }}
                    itemStyle={{ color: '#ff5722' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="avg_temperature"
                    stroke="#ff5722"
                    strokeWidth={3}
                    dot={{ r: 4, fill: '#ff5722', strokeWidth: 0 }}
                    activeDot={{ r: 6, fill: '#fff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div>
            <h3 className="text-[10px] font-bold text-muted mb-4 uppercase tracking-[0.1em] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-500"></span> PRECIPITACIÓN MEDIA (MM)
            </h3>
            <div className="h-[150px] w-full">
              <ResponsiveContainer>
                <BarChart data={monthlyData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#10101e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '11px' }}
                    cursor={{ fill: 'rgba(255,87,34,0.05)' }}
                  />
                  <Bar dataKey="avg_precipitation" radius={[4, 4, 0, 0]}>
                    {monthlyData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#00e5a0' : 'rgba(0,229,160,0.6)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* ── Ingestion Logs ─────────────────────────────────── */}
      <div className="pt-4">
        <h3 className="text-[10px] font-bold text-muted mb-4 uppercase tracking-[0.2em]">RITMO DE INGESTA</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {ingestionLogs.map(log => {
            const isSuccess = log.status === 'success';
            return (
              <div key={log.id} className="flex items-center justify-between text-[11px] glass-card p-3" style={{ borderLeftWidth: 2, borderLeftColor: isSuccess ? '#00e5a0' : '#ef4444' }}>
                <div className="flex items-center gap-3">
                  <div
                    className="w-2 h-2 rounded-full animate-pulse"
                    style={{ background: isSuccess ? '#00e5a0' : '#ef4444', boxShadow: `0 0 8px ${isSuccess ? '#00e5a0' : '#ef4444'}` }}
                  ></div>
                  <div>
                    <span className="font-bold text-white block uppercase tracking-wider">{log.source}</span>
                    <span className="text-[9px] text-muted">{log.task_name}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-mono">{log.records_inserted} REC</div>
                  <div className="text-[9px] text-muted">{new Date(log.started_at).toLocaleTimeString('es-ES')}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Model Insights ─────────────────────────────────── */}
      {modelMetrics?.metrics?.feature_importances && (
        <div className="pt-4">
          <h3 className="text-[10px] font-bold text-muted mb-4 uppercase tracking-[0.2em]">IMPORTANCIA DE VARIABLES</h3>
          <div className="space-y-2">
            {Object.entries(modelMetrics.metrics.feature_importances)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 8)
              .map(([feat, imp]) => (
                <div key={feat} className="flex flex-col gap-1">
                  <div className="flex justify-between text-[9px] font-bold uppercase tracking-wider">
                    <span className="text-white">{feat.replace('_', ' ')}</span>
                    <span className="text-accent-500">{(imp * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-brand-500 to-brand-300"
                      style={{ width: `${(imp * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard: React.FC<{ title: string; value: string; icon: any; color: string }> = ({ title, value, icon, color }) => (
  <div className="stat-card flex flex-col gap-2">
    <div className="flex items-center justify-between">
      <span className="text-[9px] font-bold text-muted tracking-widest leading-none">{title}</span>
      <Icon name={icon} size={14} style={{ color }} />
    </div>
    <div className="text-sm font-bold text-white tracking-wide">{value}</div>
  </div>
);
