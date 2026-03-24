import axios from 'axios';

const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org/search';

export async function geocodeAddress(address: string): Promise<{ lat: number; lon: number; display_name: string }[]> {
  const params = {
    q: address,
    format: 'json',
    addressdetails: 1,
    limit: 5,
  };
  const response = await axios.get(NOMINATIM_BASE_URL, { params });
  return response.data.map((item: any) => ({
    lat: parseFloat(item.lat),
    lon: parseFloat(item.lon),
    display_name: item.display_name,
  }));
}
