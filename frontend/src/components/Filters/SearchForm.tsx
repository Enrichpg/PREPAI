import React, { useState } from 'react';
import { format } from 'date-fns';
import type { RecommendationRequest, SurfaceType, ElevationProfile } from '../../types';
import { geocodeAddress } from '../../services/nominatim';

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

export const SearchForm: React.FC<Props> = ({ onSearch, loading, userPosition, setSearchedPosition }) => {
  const today = format(new Date(), 'yyyy-MM-dd');

  const [form, setForm] = useState({
    target_distance_km: '',
    target_duration_min: '',
    preferred_surface: 'mixed' as SurfaceType,
    preferred_elevation: 'flat' as ElevationProfile,
    start_lat: userPosition?.[0]?.toString() || '43.3623',
    start_lon: userPosition?.[1]?.toString() || '-8.4115',
    date: today,
    time_start: 7,
    time_end: 9,
    max_results: 5,
    search_radius_km: 30,
    address: '',
  });
  const [addressResults, setAddressResults] = useState<{ lat: number; lon: number; display_name: string }[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  React.useEffect(() => {
    if (userPosition) {
      setForm(f => ({ ...f, start_lat: userPosition[0].toString(), start_lon: userPosition[1].toString() }));
    }
  }, [userPosition]);

  const handleAddressChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setForm(f => ({ ...f, address: value }));
    if (value.length > 2) {
      const results = await geocodeAddress(value);
      setAddressResults(results);
      setShowSuggestions(true);
    } else {
      setAddressResults([]);
      setShowSuggestions(false);
    }
  };

  const handleSelectAddress = (result: { lat: number; lon: number; display_name: string }) => {
    setForm(f => ({ ...f, start_lat: result.lat.toString(), start_lon: result.lon.toString(), address: result.display_name }));
    setShowSuggestions(false);
    if (setSearchedPosition) setSearchedPosition([result.lat, result.lon]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (setSearchedPosition) setSearchedPosition([parseFloat(form.start_lat), parseFloat(form.start_lon)]);
    const req: RecommendationRequest = {
      preferred_surface: form.preferred_surface,
      preferred_elevation: form.preferred_elevation,
      start_lat: parseFloat(form.start_lat),
      start_lon: parseFloat(form.start_lon),
      date: form.date,
      time_start: form.time_start,
      time_end: form.time_end,
      max_results: form.max_results,
      search_radius_km: form.search_radius_km,
    };
    if (form.target_distance_km) req.target_distance_km = parseFloat(form.target_distance_km);
    if (form.target_duration_min) req.target_duration_min = parseInt(form.target_duration_min);
    onSearch(req);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-bold text-gray-800">Buscar rutas</h2>

      {/* Address search */}
      <div>
        <label htmlFor="address" className="block text-xs font-medium text-gray-600 mb-1">Buscar dirección o lugar</label>
        <input
          id="address"
          type="text"
          value={form.address}
          onChange={handleAddressChange}
          placeholder="Ej. Plaza de María Pita, A Coruña"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          autoComplete="off"
        />
        {showSuggestions && addressResults.length > 0 && (
          <ul className="bg-white border border-gray-200 rounded-lg mt-1 max-h-40 overflow-y-auto shadow-lg z-10 absolute w-full">
            {addressResults.map((r, i) => (
              <li
                key={i}
                className="px-3 py-2 hover:bg-green-100 cursor-pointer text-sm"
                onClick={() => handleSelectAddress(r)}
              >
                {r.display_name}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Distance / Duration */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="target_distance_km" className="block text-xs font-medium text-gray-600 mb-1">Distancia (km)</label>
          <input
            id="target_distance_km"
            type="number"
            min="1"
            max="100"
            step="0.5"
            placeholder="Ej. 10"
            value={form.target_distance_km}
            onChange={e => setForm(f => ({ ...f, target_distance_km: e.target.value }))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="target_duration_min" className="block text-xs font-medium text-gray-600 mb-1">Duración (min)</label>
          <input
            id="target_duration_min"
            type="number"
            min="10"
            max="600"
            step="5"
            placeholder="Ej. 60"
            value={form.target_duration_min}
            onChange={e => setForm(f => ({ ...f, target_duration_min: e.target.value }))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Surface */}
      <div>
        <label htmlFor="preferred_surface" className="block text-xs font-medium text-gray-600 mb-1">Superficie</label>
        <select
          id="preferred_surface"
          value={form.preferred_surface}
          onChange={e => setForm(f => ({ ...f, preferred_surface: e.target.value as SurfaceType }))}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
        >
          <option value="mixed">Mixta</option>
          <option value="asphalt">Asfalto</option>
          <option value="trail">Trail</option>
          <option value="gravel">Gravilla</option>
        </select>
      </div>

      {/* Elevation */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Desnivel</label>
        <div className="grid grid-cols-3 gap-2">
          {(['flat', 'moderate', 'hilly'] as ElevationProfile[]).map(v => (
            <button
              key={v}
              type="button"
              onClick={() => setForm(f => ({ ...f, preferred_elevation: v }))}
              className={`rounded-lg border py-2 text-xs font-medium transition-colors
                ${form.preferred_elevation === v
                  ? 'border-green-600 bg-green-600 text-white'
                  : 'border-gray-300 text-gray-600 hover:border-green-400'}`}
            >
              {v === 'flat' ? '🏃 Llano' : v === 'moderate' ? '⛰ Moderado' : '🏔 Montaña'}
            </button>
          ))}
        </div>
      </div>

      {/* Date */}
      <div>
        <label htmlFor="date" className="block text-xs font-medium text-gray-600 mb-1">Fecha</label>
        <input
          id="date"
          type="date"
          value={form.date}
          min={today}
          onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
        />
      </div>

      {/* Time Window */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="time_start" className="block text-xs font-medium text-gray-600 mb-1">Desde</label>
          <select
            id="time_start"
            value={form.time_start}
            onChange={e => setForm(f => ({ ...f, time_start: parseInt(e.target.value) }))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          >
            {HOUR_OPTIONS.map(h => (
              <option key={h.value} value={h.value}>{h.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="time_end" className="block text-xs font-medium text-gray-600 mb-1">Hasta</label>
          <select
            id="time_end"
            value={form.time_end}
            onChange={e => setForm(f => ({ ...f, time_end: parseInt(e.target.value) }))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          >
            {HOUR_OPTIONS.filter(h => h.value > form.time_start).map(h => (
              <option key={h.value} value={h.value}>{h.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Start coordinates */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="start_lat" className="block text-xs font-medium text-gray-600 mb-1">Latitud</label>
          <input
            id="start_lat"
            type="number"
            step="0.0001"
            value={form.start_lat}
            onChange={e => setForm(f => ({ ...f, start_lat: e.target.value }))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="start_lon" className="block text-xs font-medium text-gray-600 mb-1">Longitud</label>
          <input
            id="start_lon"
            type="number"
            step="0.0001"
            value={form.start_lon}
            onChange={e => setForm(f => ({ ...f, start_lon: e.target.value }))}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Radius */}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">
          Radio de búsqueda: {form.search_radius_km} km
        </label>
        <input
          type="range"
          min="5"
          max="80"
          step="5"
          value={form.search_radius_km}
          onChange={e => setForm(f => ({ ...f, search_radius_km: parseInt(e.target.value) }))}
          className="w-full accent-green-600"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-lg bg-green-600 px-4 py-3 font-semibold text-white
          hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60 transition-colors"
      >
        {loading ? 'Buscando...' : 'Buscar rutas'}
      </button>
    </form>
  );
};
