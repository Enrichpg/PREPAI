import React from 'react';
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { HourlyComfortForecast } from '../../types';
import { comfortColor } from '../../utils/comfort';

interface Props {
  data: HourlyComfortForecast[];
}

export const HourlyComfortChart: React.FC<Props> = ({ data }) => {
  return (
    <div className="h-24 w-full">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 5, right: 0, left: 0, bottom: 0 }} barGap={2}>
          <XAxis
            dataKey="hour"
            tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(h: number) => `${h}h`}
          />
          <YAxis hide domain={[0, 100]} />
          <Tooltip
            contentStyle={{
              background: '#161628',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              fontSize: '10px',
              padding: '4px 8px',
            }}
            itemStyle={{ fontWeight: 700 }}
            labelFormatter={(h: number) => `Hora: ${h}:00`}
            formatter={(val: number) => [Math.round(val), 'Índice Confort']}
          />
          <Bar dataKey="comfort_score" radius={[2, 2, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={comfortColor(entry.comfort_score)} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
