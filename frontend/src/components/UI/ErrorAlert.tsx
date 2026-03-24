import React from 'react';

interface Props {
  message: string;
  onDismiss?: () => void;
}

export const ErrorAlert: React.FC<Props> = ({ message, onDismiss }) => (
  <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
    <span className="text-lg">⚠️</span>
    <div className="flex-1 text-sm">{message}</div>
    {onDismiss && (
      <button onClick={onDismiss} className="text-red-600 hover:text-red-800 font-bold">
        ✕
      </button>
    )}
  </div>
);
