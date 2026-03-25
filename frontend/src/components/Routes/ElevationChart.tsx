import React from 'react';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

interface Props {
  data: { distance: number; altitude: number }[];
}

export const ElevationChart: React.FC<Props> = ({ data }) => {
  // Use the data as is or map if necessary. Recharts can handle the array of objects.
  const chartData = data;

  return (
    <div className="h-24 w-full">
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gradientElevation" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff5722" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ff5722" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Tooltip
            contentStyle={{
              background: '#161628',
              border: '1px solid rgba(255,87,34,0.3)',
              borderRadius: '8px',
              fontSize: '10px',
              padding: '4px 8px',
            }}
            labelStyle={{ display: 'none' }}
            itemStyle={{ color: '#ff7035', fontWeight: 700 }}
            formatter={(val: number) => [`${Math.round(val)}m`, 'Elevación']}
          />
          <Area
            type="monotone"
            dataKey="altitude"
            stroke="#ff5722"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#gradientElevation)"
          />
          <XAxis dataKey="distance" hide />
          <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
