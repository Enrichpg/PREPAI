import React from 'react';
import { Icon } from './Icon';

interface Props {
  message: string;
  onDismiss?: () => void;
}

export const ErrorAlert: React.FC<Props> = ({ message, onDismiss }) => (
  <div
    className="flex items-start gap-3 rounded-xl p-4 animate-fade-up"
    style={{
      background: 'rgba(239, 68, 68, 0.1)',
      border: '1px solid rgba(239, 68, 68, 0.3)',
      color: '#fca5a5',
      backdropFilter: 'blur(8px)',
      WebkitBackdropFilter: 'blur(8px)',
    }}
  >
    <Icon name="alert" size={18} style={{ color: '#ef4444', flexShrink: 0 }} />
    <div className="flex-1 text-sm font-medium leading-tight">{message}</div>
    {onDismiss && (
      <button
        onClick={onDismiss}
        className="hover:text-white transition-all p-1"
        style={{ color: 'rgba(239,68,68,0.7)' }}
      >
        <Icon name="close" size={14} />
      </button>
    )}
  </div>
);
