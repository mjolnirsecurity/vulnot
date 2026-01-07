'use client';

import { cn } from '@/lib/utils';

interface SensorDisplayProps {
  label: string;
  value: number;
  unit: string;
  min?: number;
  max?: number;
  decimals?: number;
  size?: 'sm' | 'md' | 'lg';
}

export function SensorDisplay({ 
  label, 
  value, 
  unit, 
  min, 
  max, 
  decimals = 1,
  size = 'md' 
}: SensorDisplayProps) {
  const isWarning = (min !== undefined && value < min) || (max !== undefined && value > max);
  
  const sizeClasses = {
    sm: 'p-2',
    md: 'p-3',
    lg: 'p-4',
  };
  
  const valueSizes = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-3xl',
  };
  
  return (
    <div className={cn(
      'bg-gray-800 rounded-lg border',
      isWarning ? 'border-red-500 bg-red-500/10' : 'border-gray-700',
      sizeClasses[size]
    )}>
      <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className={cn(
        'font-bold font-mono',
        isWarning ? 'text-red-400' : 'text-white',
        valueSizes[size]
      )}>
        {value.toFixed(decimals)}
        <span className="text-sm text-gray-400 ml-1">{unit}</span>
      </div>
      {(min !== undefined || max !== undefined) && (
        <div className="text-xs text-gray-500 mt-1">
          {min !== undefined && <span>Min: {min}</span>}
          {min !== undefined && max !== undefined && <span> | </span>}
          {max !== undefined && <span>Max: {max}</span>}
        </div>
      )}
    </div>
  );
}
