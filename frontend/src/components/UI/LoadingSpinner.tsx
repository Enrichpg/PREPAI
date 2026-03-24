import React from 'react';

interface Props {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<Props> = ({ message = 'Cargando...', size = 'md' }) => {
  const sizes = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' };
  return (
    <div className="flex flex-col items-center justify-center gap-2 p-4">
      <div
        className={`${sizes[size]} animate-spin rounded-full border-4 border-green-200 border-t-green-600`}
      />
      {message && <p className="text-sm text-gray-500">{message}</p>}
    </div>
  );
};
