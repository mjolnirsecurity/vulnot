'use client';

import { motion } from 'framer-motion';
import { getLevelColor } from '@/lib/utils';

interface TankProps {
  name: string;
  level: number;
  capacity?: number;
  unit?: string;
  inflow?: number;
  outflow?: number;
}

export function Tank({ name, level, capacity = 1000, unit = 'gal', inflow = 0, outflow = 0 }: TankProps) {
  const color = getLevelColor(level);
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h3 className="text-sm font-medium text-gray-300 mb-2 capitalize">
        {name.replace(/_/g, ' ')}
      </h3>
      
      <div className="relative w-full h-32 bg-gray-900 rounded border-2 border-gray-600 overflow-hidden">
        {/* Water level */}
        <motion.div
          className="absolute bottom-0 left-0 right-0"
          style={{ backgroundColor: color }}
          initial={{ height: 0 }}
          animate={{ height: `${level}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
        
        {/* Wave animation */}
        <div className="absolute bottom-0 left-0 right-0 overflow-hidden" style={{ height: `${level}%` }}>
          <motion.div
            className="absolute w-[200%] h-4"
            style={{
              bottom: '100%',
              background: `linear-gradient(90deg, transparent, ${color}80, transparent)`,
            }}
            animate={{ x: ['-50%', '0%'] }}
            transition={{ repeat: Infinity, duration: 2, ease: 'linear' }}
          />
        </div>
        
        {/* Level text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-white drop-shadow-lg">
            {level.toFixed(1)}%
          </span>
        </div>
      </div>
      
      {/* Flow indicators */}
      <div className="flex justify-between mt-2 text-xs text-gray-400">
        <span>In: {inflow.toFixed(0)} GPM</span>
        <span>Out: {outflow.toFixed(0)} GPM</span>
      </div>
    </div>
  );
}
