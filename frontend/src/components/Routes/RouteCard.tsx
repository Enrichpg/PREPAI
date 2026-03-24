import React, { useState } from 'react';
import type { RouteRecommendationOut } from '../../types';
import { ComfortBadge } from '../UI/ComfortBadge';
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

export const RouteCard: React.FC<Props> = ({ recommendation, onSelect, onSave, isSelected }) => {
  const { route, comfort_score, overall_score, warnings, weather_summary, hourly_comfort, rank } = recommendation;
  const [showDetails, setShowDetails] = useState(false);

  const rankColors = ['bg-yellow-400', 'bg-gray-300', 'bg-orange-400'];
  const rankBg = rankColors[rank - 1] || 'bg-gray-100';

  return (
    <div
      className={`rounded-xl border-2 transition-all cursor-pointer
        ${isSelected ? 'border-green-600 shadow-lg' : 'border-transparent shadow hover:shadow-md'}`}
      onClick={() => onSelect(recommendation)}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className={`${rankBg} rounded-full w-7 h-7 flex items-center justify-center text-xs font-bold`}>
              {rank}
            </span>
            <div>
              <h3 className="font-semibold text-gray-900 text-sm leading-tight">{route.name}</h3>
              {route.municipality && (
                <p className="text-xs text-gray-500">{route.municipality}</p>
              )}
            </div>
          </div>
          <ComfortBadge score={comfort_score} size="sm" showLabel={false} />
        </div>

        {/* Stats row */}
        <div className="flex flex-wrap gap-3 text-xs text-gray-600 mb-3">
          <span>📏 {route.distance_km.toFixed(1)} km</span>
          {route.estimated_duration_min && (
            <span>⏱ {formatDuration(route.estimated_duration_min)}</span>
          )}
          <span>🏃 {surfaceLabel(route.surface_type)}</span>
          <span>⛰ {elevationLabel(route.elevation_profile)}</span>
          {route.elevation_gain && (
            <span>↑ {Math.round(route.elevation_gain)}m</span>
          )}
        </div>

        {/* Weather summary */}
        {weather_summary && weather_summary.temp_avg !== null && (
          <div className="flex flex-wrap gap-2 text-xs text-gray-600 mb-3">
            <span>🌡 {weather_summary.temp_min?.toFixed(0)}-{weather_summary.temp_max?.toFixed(0)}°C</span>
            <span>💧 {weather_summary.precipitation_total.toFixed(1)}mm</span>
            <span>💨 {weather_summary.max_wind_speed.toFixed(0)} km/h</span>
            {weather_summary.has_fog && <span>🌫 Niebla</span>}
          </div>
        )}

        {/* Warnings */}
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

        {/* Overall score */}
        <div className="flex items-center justify-between">
          <div className="flex gap-1">
            <button
              onClick={e => { e.stopPropagation(); setShowDetails(!showDetails); }}
              className="text-xs text-blue-600 hover:underline"
            >
              {showDetails ? 'Ocultar detalles' : 'Ver detalles'}
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={e => { e.stopPropagation(); onSave(route.id); }}
              className="text-xs text-gray-500 hover:text-green-600 transition-colors"
              title="Guardar ruta"
            >
              ♡ Guardar
            </button>
            <span className="text-xs font-bold text-green-700">
              {overall_score.toFixed(0)} pts
            </span>
          </div>
        </div>
      </div>

      {/* Expanded details */}
      {showDetails && (
        <div className="border-t border-gray-100 p-4 space-y-4" onClick={e => e.stopPropagation()}>
          {route.elevation_data && route.elevation_data.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1">Perfil de elevación</p>
              <ElevationChart data={route.elevation_data} />
            </div>
          )}
          {hourly_comfort && hourly_comfort.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-600 mb-1">Comodidad por hora</p>
              <HourlyComfortChart data={hourly_comfort} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
