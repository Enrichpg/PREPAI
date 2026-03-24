import React, { useEffect, useRef } from 'react';
import {
  MapContainer, TileLayer, Polyline, CircleMarker, Popup,
  useMap, ZoomControl, LayersControl
} from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { RouteRecommendationOut, HeatmapPoint } from '../../types';
import { comfortColor, comfortLabel, surfaceLabel } from '../../utils/comfort';

// Fix default icon paths for webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// A Coruña city center
const ACORUNA_CENTER: [number, number] = [43.3623, -8.4115];

interface Props {
  recommendations: RouteRecommendationOut[];
  heatmap: HeatmapPoint[];
  selectedRec: RouteRecommendationOut | null;
  onSelectRec: (rec: RouteRecommendationOut) => void;
  userPosition: [number, number] | null;
  showHeatmap: boolean;
  searchedPosition?: [number, number] | null;
}

function FlyToSelected({ rec }: { rec: RouteRecommendationOut | null }) {
  const map = useMap();
  useEffect(() => {
    if (rec?.route.geojson) {
      const coords = rec.route.geojson.geometry.coordinates;
      if (coords.length > 0) {
        const bounds = L.latLngBounds(coords.map(([lon, lat]) => [lat, lon] as [number, number]));
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }
  }, [rec, map]);
  return null;
}

export const MapView: React.FC<Props> = ({
  recommendations, heatmap, selectedRec,
  onSelectRec, userPosition, showHeatmap, searchedPosition
}) => {
  return (
    <MapContainer
      center={userPosition || ACORUNA_CENTER}
      zoom={11}
      style={{ width: '100%', height: '100%' }}
      zoomControl={false}
    >
      <ZoomControl position="topright" />
      <FlyToSelected rec={selectedRec} />

      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="OpenStreetMap">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Satélite (Esri)">
          <TileLayer
            attribution="Tiles &copy; Esri"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
        </LayersControl.BaseLayer>
      </LayersControl>

      {/* Heatmap circles */}
      {showHeatmap && heatmap.map(pt => {
        if (!pt.lat || !pt.lon || pt.avg_comfort === null) return null;
        const color = comfortColor(pt.avg_comfort);
        return (
          <CircleMarker
            key={pt.zone_id}
            center={[pt.lat, pt.lon]}
            radius={20}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.45, weight: 1 }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-semibold">{pt.zone_name}</p>
                <p>Comodidad media: <strong>{pt.avg_comfort?.toFixed(0)}</strong>/100</p>
                <p>{comfortLabel(pt.avg_comfort)}</p>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}

      {/* Route polylines */}
      {recommendations.map(rec => {
        const coords = rec.route.geojson?.geometry.coordinates;
        if (!coords) return null;
        const latLngs = coords.map(([lon, lat]) => [lat, lon] as [number, number]);
        const isSelected = selectedRec?.route.id === rec.route.id;
        const color = comfortColor(rec.comfort_score);

        return (
          <Polyline
            key={rec.route.id}
            positions={latLngs}
            pathOptions={{
              color: isSelected ? '#16a34a' : color,
              weight: isSelected ? 6 : 3,
              opacity: isSelected ? 1 : 0.65,
              dashArray: isSelected ? undefined : '6 4',
            }}
            eventHandlers={{ click: () => onSelectRec(rec) }}
          >
            <Popup>
              <div className="text-sm min-w-[180px]">
                <p className="font-bold text-base mb-1">{rec.route.name}</p>
                <p>📏 {rec.route.distance_km.toFixed(1)} km</p>
                <p>🏃 {surfaceLabel(rec.route.surface_type)}</p>
                <p>Comodidad: <strong>{rec.comfort_score.toFixed(0)}/100</strong></p>
                {rec.warnings.length > 0 && (
                  <p className="text-orange-600 mt-1">{rec.warnings[0].message}</p>
                )}
              </div>
            </Popup>
          </Polyline>
        );
      })}

      {/* User position marker */}
      {userPosition && (
        <CircleMarker
          center={userPosition}
          radius={8}
          pathOptions={{ color: '#2563eb', fillColor: '#3b82f6', fillOpacity: 0.9, weight: 2 }}
        >
          <Popup>Tu ubicación</Popup>
        </CircleMarker>
      )}

      {/* Searched address marker */}
      {searchedPosition && (
        <CircleMarker
          center={searchedPosition}
          radius={10}
          pathOptions={{ color: '#f59e42', fillColor: '#fbbf24', fillOpacity: 0.8, weight: 2 }}
        >
          <Popup>Dirección seleccionada</Popup>
        </CircleMarker>
      )}
    </MapContainer>
  );
};
