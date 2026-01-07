'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface GaugeProps {
  name: string;
  tag: string;
  value: number;
  unit: string;
  min?: number;
  max?: number;
  lowAlarm?: number;
  highAlarm?: number;
  decimals?: number;
  className?: string;
}

export function Gauge({
  name,
  tag,
  value,
  unit,
  min = 0,
  max = 100,
  lowAlarm,
  highAlarm,
  decimals = 1,
  className,
}: GaugeProps) {
  const normalizedValue = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const angle = -135 + (normalizedValue / 100) * 270; // -135 to 135 degrees
  
  const isHighAlarm = highAlarm !== undefined && value >= highAlarm;
  const isLowAlarm = lowAlarm !== undefined && value <= lowAlarm;
  const isAlarm = isHighAlarm || isLowAlarm;
  
  const getValueColor = () => {
    if (isHighAlarm) return 'text-red-500';
    if (isLowAlarm) return 'text-yellow-500';
    return 'text-green-400';
  };

  return (
    <div className={cn('flex flex-col items-center', className)}>
      {/* Tag */}
      <div className="text-xs text-gray-400 mb-1 font-mono">{tag}</div>
      
      {/* Gauge */}
      <div className={cn(
        'relative w-24 h-16 overflow-hidden',
        isAlarm && 'animate-pulse'
      )}>
        <svg viewBox="0 0 100 60" className="w-full h-full">
          {/* Background arc */}
          <path
            d="M 10 55 A 40 40 0 0 1 90 55"
            fill="none"
            stroke="#374151"
            strokeWidth="8"
            strokeLinecap="round"
          />
          
          {/* Value arc */}
          <motion.path
            d="M 10 55 A 40 40 0 0 1 90 55"
            fill="none"
            stroke={isHighAlarm ? '#ef4444' : isLowAlarm ? '#eab308' : '#22c55e'}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${normalizedValue * 1.26} 126`}
            initial={{ strokeDasharray: '0 126' }}
            animate={{ strokeDasharray: `${normalizedValue * 1.26} 126` }}
            transition={{ duration: 0.5 }}
          />
          
          {/* Alarm zones */}
          {highAlarm !== undefined && (
            <path
              d="M 10 55 A 40 40 0 0 1 90 55"
              fill="none"
              stroke="#ef444433"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${(100 - ((highAlarm - min) / (max - min)) * 100) * 1.26} 126`}
              strokeDashoffset={`-${((highAlarm - min) / (max - min)) * 100 * 1.26}`}
            />
          )}
          
          {/* Needle */}
          <motion.line
            x1="50"
            y1="55"
            x2="50"
            y2="20"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            style={{ transformOrigin: '50px 55px' }}
            initial={{ rotate: -135 }}
            animate={{ rotate: angle }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
          
          {/* Center dot */}
          <circle cx="50" cy="55" r="4" fill="white" />
          
          {/* Min/Max labels */}
          <text x="10" y="58" fill="#9ca3af" fontSize="8" textAnchor="middle">
            {min}
          </text>
          <text x="90" y="58" fill="#9ca3af" fontSize="8" textAnchor="middle">
            {max}
          </text>
        </svg>
      </div>
      
      {/* Value Display */}
      <div className={cn(
        'text-xl font-mono font-bold -mt-2',
        getValueColor()
      )}>
        {value.toFixed(decimals)}
        <span className="text-sm text-gray-400 ml-1">{unit}</span>
      </div>
      
      {/* Name */}
      <div className="text-xs text-gray-300 mt-1 text-center">
        {name}
      </div>
    </div>
  );
}


// Simple digital display for values
interface DigitalDisplayProps {
  name: string;
  tag: string;
  value: number;
  unit: string;
  decimals?: number;
  lowAlarm?: number;
  highAlarm?: number;
  className?: string;
}

export function DigitalDisplay({
  name,
  tag,
  value,
  unit,
  decimals = 1,
  lowAlarm,
  highAlarm,
  className,
}: DigitalDisplayProps) {
  const isHighAlarm = highAlarm !== undefined && value >= highAlarm;
  const isLowAlarm = lowAlarm !== undefined && value <= lowAlarm;
  const isAlarm = isHighAlarm || isLowAlarm;
  
  const getValueColor = () => {
    if (isHighAlarm) return 'text-red-500 bg-red-500/10';
    if (isLowAlarm) return 'text-yellow-500 bg-yellow-500/10';
    return 'text-green-400 bg-green-500/10';
  };

  return (
    <div className={cn('flex flex-col', className)}>
      <div className="text-xs text-gray-400 font-mono">{tag}</div>
      <div className={cn(
        'px-3 py-1 rounded font-mono text-lg font-bold',
        getValueColor(),
        isAlarm && 'animate-pulse'
      )}>
        {value.toFixed(decimals)} {unit}
      </div>
      <div className="text-xs text-gray-300 mt-1">{name}</div>
    </div>
  );
}
