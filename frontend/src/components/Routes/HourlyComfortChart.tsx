import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import { comfortColor } from '../../utils/comfort';
import type { HourlyComfortForecast } from '../../types';

interface Props {
  data: HourlyComfortForecast[];
}

export const HourlyComfortChart: React.FC<Props> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={90}>
      <BarChart data={data} margin={{ top: 0, right: 5, left: -20, bottom: 0 }}>
        <XAxis
          dataKey="hour"
          tickFormatter={v => `${String(v).padStart(2, '0')}h`}
          tick={{ fontSize: 9 }}
        />
        <YAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
        <Tooltip
          formatter={(val: number) => [`${val.toFixed(0)}/100`, 'Comodidad']}
          labelFormatter={v => `${String(v).padStart(2, '0')}:00`}
        />
        <Bar dataKey="comfort_score" radius={[3, 3, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={index} fill={comfortColor(entry.comfort_score)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};
