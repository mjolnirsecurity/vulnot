'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useProcessStore } from '@/stores/processStore';

interface TrendChartProps {
  tag: string;
  label: string;
  color?: string;
  min?: number;
  max?: number;
  unit?: string;
}

export function TrendChart({ tag, label, color = '#3B82F6', min, max, unit = '' }: TrendChartProps) {
  const trends = useProcessStore((state) => state.trends[tag] || []);
  
  const data = trends.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString(),
    value: point.value,
  }));

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-300 mb-2">{label}</h3>
      
      <div className="h-32">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              axisLine={{ stroke: '#374151' }}
              tickLine={{ stroke: '#374151' }}
            />
            <YAxis 
              domain={[min || 'auto', max || 'auto']}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              axisLine={{ stroke: '#374151' }}
              tickLine={{ stroke: '#374151' }}
              width={40}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
              labelStyle={{ color: '#9CA3AF' }}
              formatter={(value: number) => [`${value.toFixed(2)} ${unit}`, label]}
            />
            {min !== undefined && (
              <ReferenceLine y={min} stroke="#EF4444" strokeDasharray="3 3" />
            )}
            {max !== undefined && (
              <ReferenceLine y={max} stroke="#EF4444" strokeDasharray="3 3" />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
