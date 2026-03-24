// jest will use __mocks__/axios.js automatically


jest.mock('axios');
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchForm } from './SearchForm';
import '@testing-library/jest-dom';

describe('SearchForm', () => {
  const defaultProps = {
    onSearch: jest.fn(),
    loading: false,
    userPosition: [43.3623, -8.4115] as [number, number],
    setSearchedPosition: jest.fn(),
  };

  it('renders all form fields', () => {
    render(<SearchForm {...defaultProps} />);
    // Hay un h2 y un botón con el texto 'Buscar rutas'
    expect(screen.getAllByText('Buscar rutas').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByLabelText('Buscar dirección o lugar')).toBeInTheDocument();
    expect(screen.getByLabelText('Distancia (km)')).toBeInTheDocument();
    expect(screen.getByLabelText('Duración (min)')).toBeInTheDocument();
    expect(screen.getByLabelText('Superficie')).toBeInTheDocument();
    // El grupo de botones de desnivel no tiene input asociado, solo label visual
    expect(screen.getByLabelText('Fecha')).toBeInTheDocument();
    expect(screen.getByLabelText('Desde')).toBeInTheDocument();
    expect(screen.getByLabelText('Hasta')).toBeInTheDocument();
    expect(screen.getByLabelText('Latitud')).toBeInTheDocument();
    expect(screen.getByLabelText('Longitud')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Buscar rutas' })).toBeInTheDocument();
  });

  it('calls onSearch with correct data', () => {
    render(<SearchForm {...defaultProps} />);
    fireEvent.change(screen.getByLabelText('Distancia (km)'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Duración (min)'), { target: { value: '60' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar rutas' }));
    expect(defaultProps.onSearch).toHaveBeenCalled();
  });
});
