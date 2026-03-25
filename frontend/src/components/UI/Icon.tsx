import React from 'react';

export type IconName =
  | 'run' | 'map' | 'distance' | 'clock' | 'elevation' | 'surface'
  | 'temp' | 'rain' | 'wind' | 'fog' | 'heart' | 'chart' | 'sync'
  | 'alert' | 'check' | 'close' | 'heatmap' | 'mountain' | 'flat'
  | 'moderate' | 'star' | 'chevron-right' | 'search' | 'arrow-up'
  | 'robot' | 'bolt';

interface Props {
  name: IconName;
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

const paths: Record<IconName, React.ReactNode> = {
  run: (
    <g>
      {/* Running figure — head + body */}
      <circle cx="15" cy="4" r="2.5" />
      <path d="M14 9l-2 5 2 4-3 5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 9l4 2 3-2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 14l-2 2-1 4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 13l1 4 3 2" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  ),
  map: (
    <g>
      <path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6z" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="9" y1="3" x2="9" y2="18" />
      <line x1="15" y1="6" x2="15" y2="21" />
    </g>
  ),
  distance: (
    <g>
      <path d="M3 12h18" strokeLinecap="round"/>
      <circle cx="7" cy="12" r="2" />
      <circle cx="17" cy="12" r="2" />
      <path d="M3 7l2 5-2 5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M21 7l-2 5 2 5" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  clock: (
    <g>
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 7 12 12 15 15" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  elevation: (
    <g>
      <polyline points="3 18 8 10 13 14 18 6 21 9" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="18" x2="21" y2="18" />
    </g>
  ),
  surface: (
    <g>
      <path d="M3 19l5-10 4 6 3-4 4 8" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="19" x2="21" y2="19" />
    </g>
  ),
  temp: (
    <g>
      <path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" />
    </g>
  ),
  rain: (
    <g>
      <path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16.25" strokeLinecap="round"/>
      <line x1="8" y1="19" x2="8" y2="21" strokeLinecap="round"/>
      <line x1="12" y1="21" x2="12" y2="23" strokeLinecap="round"/>
      <line x1="16" y1="19" x2="16" y2="21" strokeLinecap="round"/>
    </g>
  ),
  wind: (
    <g>
      <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  fog: (
    <g>
      <path d="M3 10h18M3 6h18M3 14h12M3 18h8" strokeLinecap="round"/>
    </g>
  ),
  heart: (
    <g>
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </g>
  ),
  chart: (
    <g>
      <line x1="18" y1="20" x2="18" y2="10" strokeLinecap="round"/>
      <line x1="12" y1="20" x2="12" y2="4"  strokeLinecap="round"/>
      <line x1="6"  y1="20" x2="6"  y2="14" strokeLinecap="round"/>
    </g>
  ),
  sync: (
    <g>
      <polyline points="23 4 23 10 17 10" strokeLinecap="round" strokeLinejoin="round"/>
      <polyline points="1 20 1 14 7 14"   strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  alert: (
    <g>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" strokeLinecap="round"/>
      <line x1="12" y1="17" x2="12.01" y2="17" strokeLinecap="round"/>
    </g>
  ),
  check: (
    <g>
      <polyline points="20 6 9 17 4 12" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  close: (
    <g>
      <line x1="18" y1="6" x2="6" y2="18" strokeLinecap="round"/>
      <line x1="6" y1="6" x2="18" y2="18" strokeLinecap="round"/>
    </g>
  ),
  heatmap: (
    <g>
      <circle cx="12" cy="12" r="3" />
      <circle cx="12" cy="12" r="6" opacity="0.5"/>
      <circle cx="12" cy="12" r="9" opacity="0.25"/>
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2" strokeLinecap="round"/>
    </g>
  ),
  mountain: (
    <g>
      <polyline points="3 20 9 8 13 13 16 10 21 20" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="20" x2="21" y2="20"/>
    </g>
  ),
  flat: (
    <g>
      <line x1="3" y1="12" x2="21" y2="12" strokeLinecap="round"/>
      <path d="M7 15l5-6 5 6" strokeLinecap="round" strokeLinejoin="round" opacity="0.4"/>
    </g>
  ),
  moderate: (
    <g>
      <polyline points="3 16 8 10 12 13 17 7 21 10" strokeLinecap="round" strokeLinejoin="round"/>
      <line x1="3" y1="20" x2="21" y2="20"/>
    </g>
  ),
  star: (
    <g>
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </g>
  ),
  'chevron-right': (
    <g>
      <polyline points="9 18 15 12 9 6" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  search: (
    <g>
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65" strokeLinecap="round"/>
    </g>
  ),
  'arrow-up': (
    <g>
      <line x1="12" y1="19" x2="12" y2="5" strokeLinecap="round"/>
      <polyline points="5 12 12 5 19 12" strokeLinecap="round" strokeLinejoin="round"/>
    </g>
  ),
  robot: (
    <g>
      <rect x="3" y="8" width="18" height="12" rx="3" ry="3"/>
      <path d="M12 3v5" strokeLinecap="round"/>
      <circle cx="12" cy="3" r="1"/>
      <circle cx="9" cy="14" r="1.5"/>
      <circle cx="15" cy="14" r="1.5"/>
      <path d="M9 18h6" strokeLinecap="round"/>
    </g>
  ),
  bolt: (
    <g>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </g>
  ),
};

export const Icon: React.FC<Props> = ({ name, size = 20, className = '', style }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.75}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={style}
    aria-hidden="true"
  >
    {paths[name]}
  </svg>
);
