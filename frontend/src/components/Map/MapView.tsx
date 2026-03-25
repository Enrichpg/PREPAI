import React, { useEffect } from 'react';
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

interface Props {
  recommendations: RouteRecommendationOut[];
  heatmap: HeatmapPoint[];
  selectedRec: RouteRecommendationOut | null;
  onSelectRec: (rec: RouteRecommendationOut) => void;
  userPosition: [number, number] | null;
  showHeatmap: boolean;
  searchedPosition?: [number, number] | null;
}

export const MapView: React.FC<Props> = ({
  recommendations, heatmap, selectedRec,
  onSelectRec, userPosition, showHeatmap, searchedPosition
}) => {
  return (
    <MapContainer
      center={userPosition || ACORUNA_CENTER}
      zoom={11}
      style={{ width: '100%', height: '100%', background: '#060609' }}
      zoomControl={false}
    >
      <ZoomControl position="topright" />
      <FlyToSelected rec={selectedRec} />

      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Gris Premium (Esri)">
          <TileLayer
            attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Negro Absoluto (Carto)">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
        </LayersControl.BaseLayer>

        <LayersControl.BaseLayer name="Satélite (Esri)">
          <TileLayer
            attribution="Tiles &copy; Esri"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Luz Inversa">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
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
            pathOptions={{ color, fillColor: color, fillOpacity: 0.3, weight: 1 }}
          >
            <Popup>
              <div style={{ color: '#f0f0f5' }}>
                <p style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '4px' }}>{pt.zone_name}</p>
                <p style={{ fontSize: '0.8rem', opacity: 0.8 }}>Confort medio: <strong>{pt.avg_comfort?.toFixed(0)}</strong>/100</p>
                <p style={{ fontSize: '0.75rem', color, fontWeight: 600 }}>{comfortLabel(pt.avg_comfort)}</p>
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
              color: isSelected ? '#ff5722' : color,
              weight: isSelected ? 6 : 4,
              opacity: isSelected ? 1 : 0.6,
              dashArray: isSelected ? undefined : '5 5',
            }}
            eventHandlers={{ click: () => onSelectRec(rec) }}
          >

            <Popup>
              <div style={{ minWidth: '160px', color: '#f0f0f5' }}>
                <p style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '4px' }}>
                  {rec.route.name}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.75rem', opacity: 0.9 }}>
                  <div>Distancia: <strong>{rec.route.distance_km?.toFixed(1) || '0.0'} km</strong></div>
                  <div>Terreno: <strong>{surfaceLabel(rec.route.surface_type)}</strong></div>
                </div>
                <p style={{ fontSize: '0.75rem', marginTop: '6px' }}>
                  Índice Confort: <strong style={{ color: comfortColor(rec.comfort_score) }}>{rec.comfort_score?.toFixed(0) || '0'}</strong>
                </p>

                {rec.warnings.length > 0 && (
                  <p style={{ color: '#ff7035', fontSize: '0.7rem', marginTop: '6px', fontStyle: 'italic' }}>
                    {rec.warnings[0].message}
                  </p>
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
          pathOptions={{ color: '#fff', fillColor: '#ff5722', fillOpacity: 1, weight: 2 }}
        >
          <Popup>Tu ubicación</Popup>
        </CircleMarker>
      )}

      {/* Searched address marker */}
      {searchedPosition && (
        <CircleMarker
          center={searchedPosition}
          radius={10}
          pathOptions={{ color: '#00e5a0', fillColor: '#00e5a0', fillOpacity: 0.4, weight: 2 }}
        >
          <Popup>Dirección seleccionada</Popup>
        </CircleMarker>
      )}
    </MapContainer>
  );
};

