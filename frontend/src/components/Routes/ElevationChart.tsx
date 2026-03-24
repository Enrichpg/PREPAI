import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts';

interface Props {
  data: Array<{ distance: number; altitude: number }>;
}

export const ElevationChart: React.FC<Props> = ({ data }) => {
  const minAlt = Math.min(...data.map(d => d.altitude));
  const maxAlt = Math.max(...data.map(d => d.altitude));

  return (
    <ResponsiveContainer width="100%" height={100}>
      <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="distance"
          tickFormatter={v => `${v.toFixed(1)}km`}
          tick={{ fontSize: 9 }}
        />
        <YAxis
          domain={[Math.max(0, minAlt - 20), maxAlt + 20]}
          tick={{ fontSize: 9 }}
          tickFormatter={v => `${v}m`}
        />
        <Tooltip
          formatter={(val: number) => [`${val.toFixed(0)}m`, 'Altitud']}
          labelFormatter={v => `${parseFloat(v).toFixed(2)} km`}
        />
        <Area
          type="monotone"
          dataKey="altitude"
          stroke="#16a34a"
          fill="#bbf7d0"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};
