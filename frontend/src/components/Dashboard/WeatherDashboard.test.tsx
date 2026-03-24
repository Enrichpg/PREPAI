import { render, screen } from '@testing-library/react';
import { WeatherDashboard } from './WeatherDashboard';
import '@testing-library/jest-dom';

describe('WeatherDashboard', () => {
  it('renders dashboard headings and stats', () => {
    render(
      <WeatherDashboard modelMetrics={null} ingestionLogs={[]} lastUpdate={null} />
    );
    expect(screen.getByText('Panel de datos')).toBeInTheDocument();
    expect(screen.getByText('Última actualización')).toBeInTheDocument();
    expect(screen.getByText('Versión modelo')).toBeInTheDocument();
  });
});
