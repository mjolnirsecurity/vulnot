'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { cn } from '@/lib/utils';

interface TrendChartProps {
  title: string;
  data: { timestamp: number; value: number }[];
  unit: string;
  color?: string;
  min?: number;
  max?: number;
  highAlarm?: number;
  lowAlarm?: number;
  className?: string;
}

export function TrendChart({
  title,
  data,
  unit,
  color = '#22c55e',
  min,
  max,
  highAlarm,
  lowAlarm,
  className,
}: TrendChartProps) {
  const formattedData = useMemo(() => {
    return data.map((point) => ({
      time: new Date(point.timestamp).toLocaleTimeString(),
      value: point.value,
      timestamp: point.timestamp,
    }));
  }, [data]);

  // Calculate domain
  const values = data.map((d) => d.value);
  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  const yMin = min ?? Math.floor(dataMin * 0.9);
  const yMax = max ?? Math.ceil(dataMax * 1.1);

  return (
    <div className={cn('bg-hmi-panel rounded-lg p-4 border border-hmi-border', className)}>
      <h3 className="text-sm font-medium text-gray-300 mb-3">{title}</h3>
      
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#6b7280" 
              fontSize={10}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis 
              stroke="#6b7280" 
              fontSize={10}
              tickLine={false}
              domain={[yMin, yMax]}
              tickFormatter={(value) => `${value}${unit}`}
              width={45}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '0.5rem',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#9ca3af' }}
              formatter={(value: number) => [`${value.toFixed(2)} ${unit}`, title]}
            />
            
            {/* High alarm line */}
            {highAlarm !== undefined && (
              <ReferenceLine 
                y={highAlarm} 
                stroke="#ef4444" 
                strokeDasharray="5 5"
                label={{ value: 'HI', fill: '#ef4444', fontSize: 10, position: 'right' }}
              />
            )}
            
            {/* Low alarm line */}
            {lowAlarm !== undefined && (
              <ReferenceLine 
                y={lowAlarm} 
                stroke="#eab308" 
                strokeDasharray="5 5"
                label={{ value: 'LO', fill: '#eab308', fontSize: 10, position: 'right' }}
              />
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
      
      {/* Current value */}
      {data.length > 0 && (
        <div className="mt-2 text-right">
          <span className="text-lg font-mono font-bold" style={{ color }}>
            {data[data.length - 1].value.toFixed(2)}
          </span>
          <span className="text-sm text-gray-400 ml-1">{unit}</span>
        </div>
      )}
    </div>
  );
}


// Multi-line trend chart
interface MultiTrendChartProps {
  title: string;
  series: {
    name: string;
    data: number[];
    color: string;
    unit: string;
  }[];
  timestamps: number[];
  className?: string;
}

export function MultiTrendChart({
  title,
  series,
  timestamps,
  className,
}: MultiTrendChartProps) {
  const formattedData = useMemo(() => {
    return timestamps.map((ts, i) => {
      const point: any = {
        time: new Date(ts).toLocaleTimeString(),
        timestamp: ts,
      };
      series.forEach((s) => {
        point[s.name] = s.data[i];
      });
      return point;
    });
  }, [timestamps, series]);

  return (
    <div className={cn('bg-hmi-panel rounded-lg p-4 border border-hmi-border', className)}>
      <h3 className="text-sm font-medium text-gray-300 mb-3">{title}</h3>
      
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              stroke="#6b7280" 
              fontSize={10}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis 
              stroke="#6b7280" 
              fontSize={10}
              tickLine={false}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '0.5rem',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#9ca3af' }}
            />
            
            {series.map((s) => (
              <Line
                key={s.name}
                type="monotone"
                dataKey={s.name}
                stroke={s.color}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Legend */}
      <div className="mt-2 flex flex-wrap gap-4">
        {series.map((s) => (
          <div key={s.name} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color }} />
            <span className="text-xs text-gray-400">{s.name}</span>
            {s.data.length > 0 && (
              <span className="text-xs font-mono" style={{ color: s.color }}>
                {s.data[s.data.length - 1]?.toFixed(1)} {s.unit}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
