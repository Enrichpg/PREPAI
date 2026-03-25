import React from 'react';
import { comfortColor, comfortLabel } from '../../utils/comfort';

interface Props {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ComfortBadge: React.FC<Props> = ({ score, size = 'md', showLabel = true }) => {
  const safeScore = score ?? 0;
  const color = comfortColor(safeScore);
  const label = comfortLabel(safeScore);


  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-3 py-1',
    lg: 'text-sm px-4 py-2',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-bold uppercase tracking-wider ${sizeClasses[size]}`}
      style={{
        backgroundColor: `${color}15`,
        color,
        border: `1px solid ${color}40`,
        backdropFilter: 'blur(4px)',
        WebkitBackdropFilter: 'blur(4px)',
      }}
    >
      <span
        className="inline-block rounded-full animate-pulse"
        style={{ width: 6, height: 6, backgroundColor: color, boxShadow: `0 0 8px ${color}` }}
      />
      {Math.round(safeScore)}

      {showLabel && <span className="font-semibold opacity-70 ml-1">· {label}</span>}
    </span>
  );
};
