import React from 'react';
import { comfortColor, comfortLabel } from '../../utils/comfort';

interface Props {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const ComfortBadge: React.FC<Props> = ({ score, size = 'md', showLabel = true }) => {
  const color = comfortColor(score);
  const label = comfortLabel(score);

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-2',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-semibold ${sizeClasses[size]}`}
      style={{ backgroundColor: `${color}20`, color }}
    >
      <span
        className="inline-block rounded-full"
        style={{ width: 8, height: 8, backgroundColor: color }}
      />
      {Math.round(score)}
      {showLabel && <span className="font-normal opacity-80">· {label}</span>}
    </span>
  );
};
