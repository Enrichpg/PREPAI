import React from 'react';

interface Props {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<Props> = ({ message = 'Cargando...', size = 'md' }) => {
  const sizes = { sm: 16, md: 32, lg: 48 };
  const s = sizes[size];

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-8 animate-fade-up">
      <div className="relative" style={{ width: s, height: s }}>
        {/* Inner ring */}
        <div
          className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand-500 animate-spin"
          style={{ animationDuration: '0.8s' }}
        />
        {/* Outer ring */}
        <div
          className="absolute -inset-1 rounded-full border border-transparent border-t-accent-500 animate-spin opacity-60"
          style={{ animationDuration: '1.2s', animationDirection: 'reverse' }}
        />
        {/* Glow */}
        <div
          className="absolute inset-1 rounded-full blur-[8px] border-none"
          style={{ background: 'rgba(255,87,34,0.15)' }}
        />
      </div>
      {message && (
        <p
          className="text-xs font-bold uppercase tracking-[0.2em] animate-pulse"
          style={{ color: 'var(--text-muted)' }}
        >
          {message}
        </p>
      )}
    </div>
  );
};
