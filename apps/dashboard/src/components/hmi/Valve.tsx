'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ValveProps {
  name: string;
  tag: string;
  position: number; // 0-100%
  type?: 'gate' | 'control' | 'check';
  onClick?: () => void;
  className?: string;
}

export function Valve({
  name,
  tag,
  position,
  type = 'control',
  onClick,
  className,
}: ValveProps) {
  const isOpen = position > 50;
  const isFullyOpen = position >= 95;
  const isFullyClosed = position <= 5;
  
  const getStatusColor = () => {
    if (isFullyOpen) return 'text-green-500 border-green-500';
    if (isFullyClosed) return 'text-red-500 border-red-500';
    return 'text-yellow-500 border-yellow-500';
  };

  return (
    <div 
      className={cn('flex flex-col items-center cursor-pointer', className)}
      onClick={onClick}
    >
      {/* Tag */}
      <div className="text-xs text-gray-400 mb-1 font-mono">{tag}</div>
      
      {/* Valve Symbol */}
      <div className={cn(
        'relative w-12 h-10 flex items-center justify-center',
        'transition-colors'
      )}>
        <svg viewBox="0 0 48 40" className="w-full h-full">
          {/* Valve Body - Two triangles */}
          <polygon 
            points="4,8 24,20 4,32" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            className={getStatusColor()}
          />
          <polygon 
            points="44,8 24,20 44,32" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2"
            className={getStatusColor()}
          />
          
          {/* Flow indicator when open */}
          {position > 10 && (
            <motion.line
              x1="4" y1="20" x2="44" y2="20"
              stroke="currentColor"
              strokeWidth="2"
              strokeDasharray="4 4"
              className="text-blue-400"
              animate={{ strokeDashoffset: [0, -16] }}
              transition={{ duration: 0.5, repeat: Infinity, ease: 'linear' }}
            />
          )}
          
          {/* Stem */}
          <line 
            x1="24" y1="20" x2="24" y2="2" 
            stroke="currentColor" 
            strokeWidth="2"
            className={getStatusColor()}
          />
          
          {/* Handwheel */}
          <motion.g
            animate={{ rotate: isOpen ? 0 : 90 }}
            transition={{ duration: 0.3 }}
            style={{ transformOrigin: '24px 2px' }}
          >
            <circle 
              cx="24" cy="2" r="4" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
              className={getStatusColor()}
            />
          </motion.g>
        </svg>
      </div>
      
      {/* Position */}
      <div className={cn(
        'text-sm font-mono font-bold',
        getStatusColor()
      )}>
        {position.toFixed(0)}%
      </div>
      
      {/* Name */}
      <div className="text-xs text-gray-300 mt-1 text-center max-w-16">
        {name}
      </div>
    </div>
  );
}
