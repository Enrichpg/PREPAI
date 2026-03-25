import React, { useState, useEffect, useRef } from 'react';
import { format } from 'date-fns';
import type { RecommendationRequest, SurfaceType, ElevationProfile } from '../../types';
import { routesApi } from '../../services/api';
import { Icon } from '../UI/Icon';


interface Props {
  onSearch: (req: RecommendationRequest) => void;
  loading: boolean;
  userPosition: [number, number] | null;
  setSearchedPosition?: (pos: [number, number] | null) => void;
}

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, i) => ({
  value: i,
  label: `${i.toString().padStart(2, '0')}:00`,
}));

const ELEVATION_OPTIONS: { value: ElevationProfile; label: string; icon: 'flat' | 'moderate' | 'mountain' }[] = [
  { value: 'flat',     label: 'Llano',    icon: 'flat'     },
  { value: 'moderate', label: 'Moderado', icon: 'moderate' },
  { value: 'hilly',    label: 'Montaña',  icon: 'mountain' },
];

export const SearchForm: React.FC<Props> = ({ onSearch, loading, userPosition, setSearchedPosition }) => {
  const today = format(new Date(), 'yyyy-MM-dd');

  const [form, setForm] = useState({
    target_distance_km: '5',
    target_duration_min: '45',

    preferred_surface: 'mixed' as SurfaceType,
    preferred_elevation: 'flat' as ElevationProfile,
    start_lat: '',
    start_lon: '',
    end_lat: '',
    end_lon: '',
    date: today,
    time_start: '7',
    time_end: '9',
    max_results: 5,
    search_radius_km: 15,
    start_address: '',
    end_address: '',
  });


  // Separate states for Origin and Arrival
  const [startResults, setStartResults] = useState<{ lat: number; lon: number; display_name: string }[]>([]);
  const [endResults, setEndResults] = useState<{ lat: number; lon: number; display_name: string }[]>([]);
  const [showStartSugg, setShowStartSugg] = useState(false);
  const [showEndSugg, setShowEndSugg] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [endError, setEndError] = useState<string | null>(null);
  const [startLoading, setStartLoading] = useState(false);
  const [endLoading, setEndLoading] = useState(false);
  
  const startTimeout = useRef<NodeJS.Timeout | null>(null);
  const endTimeout = useRef<NodeJS.Timeout | null>(null);

  const handleUseLocation = () => {
    if (userPosition) {
      setForm(f => ({ 
        ...f, 
        start_lat: userPosition[0].toString(), 
        start_lon: userPosition[1].toString(),
        start_address: 'Mi ubicación' 
      }));
      setStartError(null);
      if (setSearchedPosition) setSearchedPosition([userPosition[0], userPosition[1]]);
    }
  };

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setForm(f => ({ ...f, start_address: value }));
    setStartError(null);
    if (startTimeout.current) clearTimeout(startTimeout.current);

    if (value.length > 3) {
      setStartLoading(true);
      startTimeout.current = setTimeout(async () => {
        try {
          const results = await routesApi.geocodeAddress(value);
          setStartResults(results);
          setShowStartSugg(true);
        } catch (err) {
          setStartError('Error al buscar');
          setStartResults([]);
        } finally {
          setStartLoading(false);
        }
      }, 500);
    } else {
      setStartResults([]);
      setShowStartSugg(false);
      setStartLoading(false);
    }
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setForm(f => ({ ...f, end_address: value }));
    setEndError(null);
    if (endTimeout.current) clearTimeout(endTimeout.current);

    if (value.length > 3) {
      setEndLoading(true);
      endTimeout.current = setTimeout(async () => {
        try {
          const results = await routesApi.geocodeAddress(value);
          setEndResults(results);
          setShowEndSugg(true);
        } catch (err) {
          setEndError('Error al buscar');
          setEndResults([]);
        } finally {
          setEndLoading(false);
        }
      }, 500);
    } else {
      setEndResults([]);
      setShowEndSugg(false);
      setEndLoading(false);
    }
  };

  const handleSelectStart = (result: { lat: number; lon: number; display_name: string }) => {
    setForm(f => ({ 
      ...f, 
      start_lat: result.lat.toString(), 
      start_lon: result.lon.toString(), 
      start_address: result.display_name.split(',')[0] 
    }));
    setShowStartSugg(false);
    if (setSearchedPosition) setSearchedPosition([result.lat, result.lon]);
  };

  const handleSelectEnd = (result: { lat: number; lon: number; display_name: string }) => {
    setForm(f => ({ 
      ...f, 
      end_lat: result.lat.toString(), 
      end_lon: result.lon.toString(), 
      end_address: result.display_name.split(',')[0] 
    }));
    setShowEndSugg(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Default to A Coruña central if no start point provided
    const start_lat = parseFloat(form.start_lat) || 43.3623;
    const start_lon = parseFloat(form.start_lon) || -8.4115;

    if (setSearchedPosition) setSearchedPosition([start_lat, start_lon]);

    const req: RecommendationRequest = {
      preferred_surface: form.preferred_surface,
      preferred_elevation: form.preferred_elevation,
      start_lat,
      start_lon,
      max_results: form.max_results,
      search_radius_km: form.search_radius_km,
    };

    if (form.end_lat && form.end_lon) {
      req.end_lat = parseFloat(form.end_lat);
      req.end_lon = parseFloat(form.end_lon);
    }

    if (form.date) req.date = form.date;
    if (form.time_start) req.time_start = parseInt(form.time_start);
    if (form.time_end) req.time_end = parseInt(form.time_end);
    if (form.target_distance_km) req.target_distance_km = parseFloat(form.target_distance_km);
    if (form.target_duration_min) req.target_duration_min = parseInt(form.target_duration_min);
    
    onSearch(req);
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '0.68rem',
    fontWeight: 700,
    letterSpacing: '0.08em',
    color: 'var(--text-muted)',
    marginBottom: '0.35rem',
    textTransform: 'uppercase',
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">

      {/* Section title */}
      <div className="flex items-center gap-2 mb-1">
        <Icon name="search" size={15} style={{ color: '#ff5722' }} />
        <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
          Buscar rutas
        </span>
      </div>

      {/* Start Point */}
      <div className="relative">
        <div className="flex items-center justify-between mb-1">
          <label style={labelStyle} htmlFor="start_address">
            <span className="flex items-center gap-1">
              <Icon name="map" size={11} className="inline" /> Punto de Salida
            </span>
          </label>
          <button
            type="button"
            onClick={handleUseLocation}
            className="text-[10px] font-bold text-brand-400 hover:text-brand-300 transition-colors uppercase"
            style={{ letterSpacing: '0.05em' }}
          >
            Mi ubicación
          </button>
        </div>
        <input
          id="start_address"
          type="text"
          value={form.start_address}
          onChange={handleStartChange}
          placeholder="Plaza de María Pita..."
          className={`input-dark ${startError ? 'border-red-500/50' : ''}`}
          autoComplete="off"
        />
        {startLoading && (
          <div className="absolute right-3 top-[2.4rem]">
            <span className="w-3 h-3 border-2 border-brand-500 border-t-transparent rounded-full animate-spin inline-block"></span>
          </div>
        )}
        {showStartSugg && startResults.length > 0 && (
          <ul className="suggestions-list z-[100]">
            {startResults.map((r, i) => (
              <li key={i} onClick={() => handleSelectStart(r)}>{r.display_name}</li>
            ))}
          </ul>
        )}
      </div>

      {/* End Point */}
      <div className="relative">
        <label style={labelStyle} htmlFor="end_address">
          <span className="flex items-center gap-1">
            <Icon name="map" size={11} className="inline" /> Punto de Llegada (Opcional)
          </span>
        </label>
        <input
          id="end_address"
          type="text"
          value={form.end_address}
          onChange={handleEndChange}
          placeholder="Cualquier lugar..."
          className={`input-dark ${endError ? 'border-red-500/50' : ''}`}
          autoComplete="off"
        />
        {endLoading && (
          <div className="absolute right-3 top-[2.1rem]">
            <span className="w-3 h-3 border-2 border-brand-500 border-t-transparent rounded-full animate-spin inline-block"></span>
          </div>
        )}
        {showEndSugg && endResults.length > 0 && (
          <ul className="suggestions-list z-[60]">
            {endResults.map((r, i) => (
              <li key={i} onClick={() => handleSelectEnd(r)}>{r.display_name}</li>
            ))}
          </ul>
        )}
      </div>


      {/* Distance / Duration */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label style={labelStyle} htmlFor="target_distance_km">
            <span className="flex items-center gap-1"><Icon name="distance" size={11} className="inline" /> Km</span>
          </label>
          <input
            id="target_distance_km"
            type="number" min="1" max="100" step="0.5"
            placeholder="10"
            value={form.target_distance_km}
            onChange={e => setForm(f => ({ ...f, target_distance_km: e.target.value }))}
            className="input-dark"
          />
        </div>
        <div>
          <label style={labelStyle} htmlFor="target_duration_min">
            <span className="flex items-center gap-1"><Icon name="clock" size={11} className="inline" /> Min</span>
          </label>
          <input
            id="target_duration_min"
            type="number" min="10" max="600" step="5"
            placeholder="60"
            value={form.target_duration_min}
            onChange={e => setForm(f => ({ ...f, target_duration_min: e.target.value }))}
            className="input-dark"
          />
        </div>
      </div>

      {/* Surface */}
      <div>
        <label style={labelStyle} htmlFor="preferred_surface">
          <span className="flex items-center gap-1"><Icon name="surface" size={11} className="inline" /> Superficie</span>
        </label>
        <select
          id="preferred_surface"
          value={form.preferred_surface}
          onChange={e => setForm(f => ({ ...f, preferred_surface: e.target.value as SurfaceType }))}
          className="input-dark"
        >
          <option value="mixed">Mixta</option>
          <option value="asphalt">Asfalto</option>
          <option value="trail">Trail</option>
          <option value="gravel">Gravilla</option>
        </select>
      </div>

      {/* Elevation — visual pill buttons */}
      <div>
        <label style={labelStyle}>
          <span className="flex items-center gap-1"><Icon name="elevation" size={11} className="inline" /> Desnivel</span>
        </label>
        <div className="grid grid-cols-3 gap-2">
          {ELEVATION_OPTIONS.map(opt => {
            const active = form.preferred_elevation === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={() => setForm(f => ({ ...f, preferred_elevation: opt.value }))}
                className="flex flex-col items-center gap-1 py-2.5 rounded-xl transition-all"
                style={{
                  background: active ? 'rgba(255,87,34,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${active ? '#ff5722' : 'rgba(255,255,255,0.08)'}`,
                  color: active ? '#ff7035' : 'var(--text-muted)',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  letterSpacing: '0.04em',
                }}
              >
                <Icon name={opt.icon} size={16} />
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Date */}
      <div>
        <label style={labelStyle} htmlFor="date">
          <span className="flex items-center gap-1"><Icon name="sync" size={11} className="inline" /> Fecha</span>
        </label>
        <input
          id="date"
          type="date"
          value={form.date}
          min={today}
          onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
          className="input-dark"
        />
      </div>

      {/* Time window */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label style={labelStyle} htmlFor="time_start">
            <span className="flex items-center gap-1"><Icon name="clock" size={11} className="inline" /> Desde</span>
          </label>
          <select
            id="time_start"
            value={form.time_start}
            onChange={e => setForm(f => ({ ...f, time_start: e.target.value }))}
            className="input-dark"
          >
            <option value="">Cualquier hora</option>
            {HOUR_OPTIONS.map(h => (
              <option key={h.value} value={h.value}>{h.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label style={labelStyle} htmlFor="time_end">
            <span className="flex items-center gap-1"><Icon name="clock" size={11} className="inline" /> Hasta</span>
          </label>
          <select
            id="time_end"
            value={form.time_end}
            onChange={e => setForm(f => ({ ...f, time_end: e.target.value }))}
            className="input-dark"
          >
            <option value="">Cualquier hora</option>
            {HOUR_OPTIONS.filter(h => !form.time_start || h.value > parseInt(form.time_start)).map(h => (
              <option key={h.value} value={h.value}>{h.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Coordinates (compact) */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label style={labelStyle} htmlFor="start_lat">Latitud</label>
          <input
            id="start_lat"
            type="number" step="0.0001"
            value={form.start_lat}
            onChange={e => setForm(f => ({ ...f, start_lat: e.target.value }))}
            className="input-dark"
          />
        </div>
        <div>
          <label style={labelStyle} htmlFor="start_lon">Longitud</label>
          <input
            id="start_lon"
            type="number" step="0.0001"
            value={form.start_lon}
            onChange={e => setForm(f => ({ ...f, start_lon: e.target.value }))}
            className="input-dark"
          />
        </div>
      </div>

      {/* Radius slider */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label style={labelStyle}>
            <span className="flex items-center gap-1">
              <Icon name="distance" size={11} className="inline" /> Radio de búsqueda
            </span>
          </label>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ff7035' }}>
            {form.search_radius_km} km
          </span>
        </div>
        <input
          type="range" min="5" max="80" step="5"
          value={form.search_radius_km}
          onChange={e => setForm(f => ({ ...f, search_radius_km: parseInt(e.target.value) }))}
          style={{ width: '100%' }}
        />
      </div>

      {/* Submit */}
      <button type="submit" disabled={loading} className="btn-brand">
        {loading
          ? (
            <span className="flex items-center justify-center gap-2">
              <span
                style={{
                  width: 14, height: 14,
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderTopColor: '#fff',
                  borderRadius: '50%',
                  display: 'inline-block',
                  animation: 'spin 0.7s linear infinite',
                }}
              />
              Analizando rutas...
            </span>
          )
          : (
            <span className="flex items-center justify-center gap-2">
              <Icon name="run" size={16} />
              Encontrar rutas
            </span>
          )
        }
      </button>
    </form>
  );
};
