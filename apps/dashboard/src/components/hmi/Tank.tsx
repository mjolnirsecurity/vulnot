'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface TankProps {
  name: string;
  tag: string;
  level: number;
  unit?: string;
  maxLevel?: number;
  minLevel?: number;
  highAlarm?: number;
  lowAlarm?: number;
  className?: string;
}

export function Tank({
  name,
  tag,
  level,
  unit = '%',
  maxLevel = 100,
  minLevel = 0,
  highAlarm = 90,
  lowAlarm = 20,
  className,
}: TankProps) {
  const normalizedLevel = Math.min(100, Math.max(0, ((level - minLevel) / (maxLevel - minLevel)) * 100));
  
  const isHighAlarm = level >= highAlarm;
  const isLowAlarm = level <= lowAlarm;
  const isNormal = !isHighAlarm && !isLowAlarm;
  
  const getLevelColor = () => {
    if (isHighAlarm) return 'from-red-500 to-red-600';
    if (isLowAlarm) return 'from-yellow-500 to-yellow-600';
    return 'from-blue-400 to-blue-600';
  };
  
  const getBorderColor = () => {
    if (isHighAlarm || isLowAlarm) return 'border-red-500';
    return 'border-hmi-border';
  };

  return (
    <div className={cn('flex flex-col items-center', className)}>
      {/* Tank Name */}
      <div className="text-xs text-gray-400 mb-1 font-mono">{tag}</div>
      
      {/* Tank Container */}
      <div 
        className={cn(
          'relative w-20 h-32 rounded-b-lg border-2 border-t-0 bg-hmi-panel overflow-hidden',
          getBorderColor(),
          (isHighAlarm || isLowAlarm) && 'animate-pulse'
        )}
      >
        {/* Tank Top */}
        <div className={cn(
          'absolute -top-0.5 left-1/2 -translate-x-1/2 w-16 h-2 rounded-t border-2 border-b-0',
          getBorderColor(),
          'bg-hmi-panel'
        )} />
        
        {/* Level Indicator Marks */}
        <div className="absolute right-1 top-2 bottom-2 w-1 flex flex-col justify-between">
          {[100, 75, 50, 25, 0].map((mark) => (
            <div key={mark} className="flex items-center">
              <div className="w-2 h-px bg-gray-600" />
            </div>
          ))}
        </div>
        
        {/* Water Level */}
        <motion.div
          className={cn(
            'absolute bottom-0 left-0 right-0 bg-gradient-to-t',
            getLevelColor()
          )}
          initial={{ height: 0 }}
          animate={{ height: `${normalizedLevel}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          {/* Water Surface Animation */}
          <div className="absolute top-0 left-0 right-0 h-2 bg-white/20 animate-pulse" />
        </motion.div>
        
        {/* High/Low Alarm Lines */}
        <div 
          className="absolute left-0 right-0 h-px bg-red-500/50"
          style={{ bottom: `${((highAlarm - minLevel) / (maxLevel - minLevel)) * 100}%` }}
        />
        <div 
          className="absolute left-0 right-0 h-px bg-yellow-500/50"
          style={{ bottom: `${((lowAlarm - minLevel) / (maxLevel - minLevel)) * 100}%` }}
        />
      </div>
      
      {/* Level Value */}
      <div className={cn(
        'mt-2 text-lg font-mono font-bold',
        isHighAlarm && 'text-red-500',
        isLowAlarm && 'text-yellow-500',
        isNormal && 'text-green-400'
      )}>
        {level.toFixed(1)}{unit}
      </div>
      
      {/* Tank Name */}
      <div className="text-xs text-gray-300 mt-1 text-center max-w-20 leading-tight">
        {name}
      </div>
    </div>
  );
}
