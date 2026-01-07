'use client';

import { motion } from 'framer-motion';
import { Power } from 'lucide-react';

interface PumpProps {
  name: string;
  running: boolean;
  speed: number;
  flow: number;
  onToggle?: () => void;
}

export function Pump({ name, running, speed, flow, onToggle }: PumpProps) {
  return (
    <div className={`bg-gray-800 rounded-lg p-3 border ${running ? 'border-green-500' : 'border-gray-700'}`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-300 capitalize">
          {name.replace(/_/g, ' ')}
        </h4>
        <button
          onClick={onToggle}
          className={`p-1.5 rounded-full transition-colors ${
            running ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-500'
          }`}
        >
          <Power size={14} className="text-white" />
        </button>
      </div>
      
      {/* Pump animation */}
      <div className="flex items-center justify-center h-12 mb-2">
        <motion.div
          className={`w-10 h-10 rounded-full border-4 ${
            running ? 'border-green-500' : 'border-gray-600'
          }`}
          animate={running ? { rotate: 360 } : {}}
          transition={{ repeat: Infinity, duration: 2 / (speed / 50 || 1), ease: 'linear' }}
        >
          <div className={`w-full h-full rounded-full ${running ? 'bg-green-500/20' : 'bg-gray-700'}`} />
        </motion.div>
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="text-center">
          <div className="text-gray-500">Speed</div>
          <div className="text-white font-medium">{speed.toFixed(0)}%</div>
        </div>
        <div className="text-center">
          <div className="text-gray-500">Flow</div>
          <div className="text-white font-medium">{flow.toFixed(0)} GPM</div>
        </div>
      </div>
    </div>
  );
}
