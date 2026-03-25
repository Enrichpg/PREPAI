import React, { useState } from 'react';
import type { RouteRecommendationOut } from '../../types';
import { ComfortBadge } from '../UI/ComfortBadge';
import { Icon } from '../UI/Icon';
import {
  surfaceLabel, elevationLabel, formatDuration,
  warningIcon, severityColor
} from '../../utils/comfort';
import { ElevationChart } from './ElevationChart';
import { HourlyComfortChart } from './HourlyComfortChart';

interface Props {
  recommendation: RouteRecommendationOut;
  onSelect: (rec: RouteRecommendationOut) => void;
  onSave: (routeId: number) => void;
  isSelected: boolean;
}

/* Rank accent colors: gold / silver / bronze */
const RANK_COLORS = ['#f0a500', '#9ba3af', '#c07933'];
const RANK_LABELS = ['ORO', 'PLATA', 'BRONCE'];

export const RouteCard: React.FC<Props> = ({ recommendation, onSelect, onSave, isSelected }) => {
  const { route, comfort_score, overall_score, warnings, weather_summary, hourly_comfort, rank } = recommendation;
  const [showDetails, setShowDetails] = useState(false);
  const [saved,      setSaved]       = useState(false);

  const rankColor = RANK_COLORS[rank - 1] ?? 'rgba(255,255,255,0.2)';
  const rankLabel = RANK_LABELS[rank - 1] ?? `#${rank}`;

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSaved(true);
    onSave(route.id);
  };

  return (
    <div
      className={`glass-card${isSelected ? ' selected' : ''} cursor-pointer animate-fade-up`}
      style={{
        borderLeft: `3px solid ${rankColor}`,
        borderRadius: '14px',
      }}
      onClick={() => onSelect(recommendation)}
    >
      <div className="p-4">

        {/* ── Header ──────────────────────────────────── */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5">
            {/* Rank badge */}
            <div
              className="flex-shrink-0 flex items-center justify-center rounded-lg"
              style={{
                width: 34, height: 34,
                background: `${rankColor}18`,
                border: `1px solid ${rankColor}50`,
                color: rankColor,
                fontSize: '0.6rem',
                fontWeight: 800,
                letterSpacing: '0.08em',
              }}
            >
              {/* small chevron + rank label stacked */}
              <span>{rankLabel}</span>
            </div>
            <div>
              <h3
                style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}
              >
                {route.name}
              </h3>
              {route.municipality && (
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  {route.municipality}
                </p>
              )}
            </div>
          </div>
          <ComfortBadge score={comfort_score} size="sm" showLabel={false} />
        </div>

        {/* ── Stats row ───────────────────────────────── */}
        <div
          className="grid grid-cols-4 gap-2 mb-3 rounded-xl p-2"
          style={{ background: 'rgba(255,255,255,0.03)' }}
        >
          {[
            { icon: 'distance' as const, val: `${route.distance_km?.toFixed(1) || '0.0'} km` },
            ...(route.estimated_duration_min
              ? [{ icon: 'clock'     as const, val: formatDuration(route.estimated_duration_min) }]
              : []),
            { icon: 'surface'  as const, val: surfaceLabel(route.surface_type) },
            { icon: 'elevation' as const, val: elevationLabel(route.elevation_profile) },
          ].map((s, i) => (
            <div key={i} className="flex flex-col items-center gap-0.5">
              <Icon name={s.icon} size={13} style={{ color: '#ff5722', opacity: 0.85 }} />
              <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textAlign: 'center', lineHeight: 1.2 }}>
                {s.val}
              </span>
            </div>
          ))}
          {route.elevation_gain && (
            <div className="flex flex-col items-center gap-0.5">
              <Icon name="arrow-up" size={13} style={{ color: '#00e5a0', opacity: 0.85 }} />
              <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>
                {Math.round(route.elevation_gain)}m
              </span>
            </div>
          )}
        </div>

        {/* ── Weather ─────────────────────────────────── */}
        {weather_summary && weather_summary.temp_avg !== null && (
          <div className="flex flex-wrap gap-2 mb-3">
            {[
              { icon: 'temp' as const, val: `${weather_summary.temp_min?.toFixed(0) || '-'}-${weather_summary.temp_max?.toFixed(0) || '-'}°C` },
              { icon: 'rain' as const, val: `${weather_summary.precipitation_total?.toFixed(1) || '0.0'} mm` },
              { icon: 'wind' as const, val: `${weather_summary.max_wind_speed?.toFixed(0) || '0'} km/h` },
              ...(weather_summary.has_fog ? [{ icon: 'fog' as const, val: 'Niebla' }] : []),
            ].map((w, i) => (
              <span
                key={i}
                className="flex items-center gap-1 px-2 py-0.5 rounded-full"
                style={{
                  fontSize: '0.68rem',
                  color: 'var(--text-secondary)',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.07)',
                }}
              >
                <Icon name={w.icon} size={11} style={{ color: '#00e5a0' }} />
                {w.val}
              </span>
            ))}
          </div>
        )}

        {/* ── Warnings ────────────────────────────────── */}
        {warnings.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {warnings.map((w, i) => (
              <span
                key={i}
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${severityColor(w.severity)}`}
              >
                {warningIcon(w.type)} {w.message}
              </span>
            ))}
          </div>
        )}

        {/* ── Footer ──────────────────────────────────── */}
        <div className="flex items-center justify-between pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <button
            onClick={e => { e.stopPropagation(); setShowDetails(d => !d); }}
            className="flex items-center gap-1 transition-colors"
            style={{ fontSize: '0.72rem', color: showDetails ? '#ff5722' : 'var(--text-muted)', fontWeight: 600 }}
          >
            <Icon name="chevron-right" size={12}
              style={{ transform: showDetails ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s ease' }}
            />
            {showDetails ? 'Ocultar' : 'Detalles'}
          </button>
          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              className="flex items-center gap-1 transition-all"
              style={{
                fontSize: '0.72rem',
                color: saved ? '#ff5722' : 'var(--text-muted)',
                fontWeight: 600,
              }}
              title="Guardar ruta"
            >
              <Icon name="heart" size={13} style={{ fill: saved ? '#ff5722' : 'none', strokeWidth: saved ? 0 : 1.75 }} />
              {saved ? 'Guardada' : 'Guardar'}
            </button>
            {/* Score pill */}
            <span
              className="rounded-full px-2.5 py-0.5 font-bold"
              style={{
                fontSize: '0.72rem',
                background: 'linear-gradient(135deg, rgba(0,229,160,0.15), rgba(0,229,160,0.08))',
                color: '#00e5a0',
                border: '1px solid rgba(0,229,160,0.25)',
              }}
            >
              {overall_score?.toFixed(0) || '0'} pts
            </span>
          </div>
        </div>
      </div>

      {/* ── Expanded details ──────────────────────────── */}
      {showDetails && (
        <div
          className="px-4 pb-4 space-y-4 animate-fade-up"
          style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
          onClick={e => e.stopPropagation()}
        >
          {route.elevation_data && route.elevation_data.length > 0 && (
            <div className="pt-3">
              <p style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 6 }}>
                PERFIL DE ELEVACIÓN
              </p>
              <ElevationChart data={route.elevation_data} />
            </div>
          )}
          {hourly_comfort && hourly_comfort.length > 0 && (
            <div>
              <p style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: 6 }}>
                COMODIDAD POR HORA
              </p>
              <HourlyComfortChart data={hourly_comfort} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
