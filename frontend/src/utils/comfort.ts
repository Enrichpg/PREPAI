export function comfortColor(score: number): string {
  if (score >= 80) return '#22c55e';   // green
  if (score >= 60) return '#84cc16';   // lime
  if (score >= 45) return '#eab308';   // yellow
  if (score >= 30) return '#f97316';   // orange
  return '#ef4444';                    // red
}

export function comfortLabel(score: number): string {
  if (score >= 80) return 'Excelente';
  if (score >= 60) return 'Buena';
  if (score >= 45) return 'Aceptable';
  if (score >= 30) return 'Mala';
  return 'Muy mala';
}

export function surfaceLabel(surface: string): string {
  const map: Record<string, string> = {
    asphalt: 'Asfalto',
    trail: 'Trail',
    mixed: 'Mixto',
    gravel: 'Gravilla',
    track: 'Pista',
  };
  return map[surface] || surface;
}

export function elevationLabel(elev: string): string {
  const map: Record<string, string> = {
    flat: 'Llano',
    moderate: 'Moderado',
    hilly: 'Montañoso',
  };
  return map[elev] || elev;
}

export function warningIcon(type: string): string {
  const map: Record<string, string> = {
    rain: '🌧',
    wind: '💨',
    fog: '🌫',
    heat: '🌡',
    cold: '🥶',
    uv: '☀️',
  };
  return map[type] || '⚠️';
}

export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m} min`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}min`;
}

export function severityColor(severity: string): string {
  if (severity === 'high') return 'text-red-600 bg-red-50';
  if (severity === 'medium') return 'text-orange-600 bg-orange-50';
  return 'text-yellow-700 bg-yellow-50';
}
