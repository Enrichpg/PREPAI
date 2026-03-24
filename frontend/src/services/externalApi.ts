import axios from 'axios';

const BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1/external';

export const externalApi = {
  getCurrentWeather: (lat: number, lon: number) =>
    axios.get(`${BASE}/weather/openweathermap`, { params: { lat, lon } }).then(r => r.data),

  getAirQuality: (lat: number, lon: number) =>
    axios.get(`${BASE}/air/aqicn`, { params: { lat, lon } }).then(r => r.data),

  getEvents: (lat: number, lon: number, radius_km = 10, q?: string) =>
    axios.get(`${BASE}/events/eventbrite`, { params: { lat, lon, radius_km, q } }).then(r => r.data),

  getTraffic: (bbox: string) =>
    axios.get(`${BASE}/traffic/tomtom`, { params: { bbox } }).then(r => r.data),
};
