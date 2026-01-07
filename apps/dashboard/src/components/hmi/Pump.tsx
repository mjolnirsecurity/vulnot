'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface PumpProps {
  name: string;
  tag: string;
  running: boolean;
  speed?: number;
  fault?: boolean;
  onClick?: () => void;
  className?: string;
}

export function Pump({
  name,
  tag,
  running,
  speed = 0,
  fault = false,
  onClick,
  className,
}: PumpProps) {
  const getStatusColor = () => {
    if (fault) return 'text-red-500 border-red-500';
    if (running) return 'text-green-500 border-green-500';
    return 'text-gray-500 border-gray-500';
  };

  const getStatusText = () => {
    if (fault) return 'FAULT';
    if (running) return 'RUN';
    return 'STOP';
  };

  return (
    <div 
      className={cn('flex flex-col items-center cursor-pointer', className)}
      onClick={onClick}
    >
      {/* Tag */}
      <div className="text-xs text-gray-400 mb-1 font-mono">{tag}</div>
      
      {/* Pump Symbol */}
      <div className={cn(
        'relative w-14 h-14 rounded-full border-2 flex items-center justify-center',
        'bg-hmi-panel transition-colors',
        getStatusColor(),
        fault && 'animate-pulse'
      )}>
        {/* Pump Icon */}
        <svg 
          viewBox="0 0 24 24" 
          className={cn('w-8 h-8', getStatusColor())}
          fill="currentColor"
        >
          <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
          <motion.g
            animate={running ? { rotate: 360 } : { rotate: 0 }}
            transition={{ duration: 1, repeat: running ? Infinity : 0, ease: 'linear' }}
            style={{ transformOrigin: '12px 12px' }}
          >
            <path d="M12 4 L12 8 M12 16 L12 20 M4 12 L8 12 M16 12 L20 12" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round"
            />
          </motion.g>
        </svg>
        
        {/* Running indicator light */}
        <div className={cn(
          'absolute -top-1 -right-1 w-3 h-3 rounded-full border border-gray-600',
          running && 'bg-green-500 shadow-lg shadow-green-500/50',
          fault && 'bg-red-500 shadow-lg shadow-red-500/50 animate-blink',
          !running && !fault && 'bg-gray-600'
        )} />
      </div>
      
      {/* Status */}
      <div className={cn(
        'mt-1 text-xs font-bold font-mono',
        getStatusColor()
      )}>
        {getStatusText()}
      </div>
      
      {/* Speed */}
      {running && speed > 0 && (
        <div className="text-xs text-gray-400 font-mono">
          {speed.toFixed(0)}%
        </div>
      )}
      
      {/* Name */}
      <div className="text-xs text-gray-300 mt-1 text-center max-w-16">
        {name}
      </div>
    </div>
  );
}
