'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, AlertCircle, Info, Bell, BellOff, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useProcessStore, Alarm } from '@/lib/store';

interface AlarmPanelProps {
  className?: string;
}

export function AlarmPanel({ className }: AlarmPanelProps) {
  const { state, acknowledgeAlarm } = useProcessStore();
  const [muted, setMuted] = useState(false);
  
  const alarms = state?.alarms ?? [];
  const activeAlarms = alarms.filter((a) => !a.acknowledged);
  const hasHighAlarm = activeAlarms.some((a) => a.level === 'HIGH');

  return (
    <div className={cn(
      'bg-hmi-panel rounded-lg border',
      hasHighAlarm ? 'border-red-500' : 'border-hmi-border',
      className
    )}>
      {/* Header */}
      <div className={cn(
        'flex items-center justify-between px-4 py-2 rounded-t-lg',
        hasHighAlarm ? 'bg-red-500/20' : 'bg-hmi-border/50'
      )}>
        <div className="flex items-center gap-2">
          <Bell className={cn(
            'w-4 h-4',
            hasHighAlarm && 'text-red-500 animate-pulse'
          )} />
          <span className="text-sm font-medium text-gray-200">
            Alarms ({activeAlarms.length})
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setMuted(!muted)}
            className={cn(
              'p-1 rounded hover:bg-gray-700 transition-colors',
              muted && 'text-yellow-500'
            )}
          >
            {muted ? <BellOff className="w-4 h-4" /> : <Bell className="w-4 h-4" />}
          </button>
          
          {activeAlarms.length > 0 && (
            <button
              onClick={() => activeAlarms.forEach((a) => acknowledgeAlarm(a.tag))}
              className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
            >
              ACK ALL
            </button>
          )}
        </div>
      </div>
      
      {/* Alarm List */}
      <div className="max-h-48 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {alarms.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="px-4 py-8 text-center text-gray-500"
            >
              <Check className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p className="text-sm">No active alarms</p>
            </motion.div>
          ) : (
            alarms.map((alarm, index) => (
              <AlarmItem
                key={`${alarm.tag}-${index}`}
                alarm={alarm}
                onAcknowledge={() => acknowledgeAlarm(alarm.tag)}
              />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}


interface AlarmItemProps {
  alarm: Alarm;
  onAcknowledge: () => void;
}

function AlarmItem({ alarm, onAcknowledge }: AlarmItemProps) {
  const getAlarmStyles = () => {
    switch (alarm.level) {
      case 'HIGH':
        return {
          bg: alarm.acknowledged ? 'bg-red-500/10' : 'bg-red-500/20',
          border: 'border-l-red-500',
          icon: <AlertTriangle className="w-4 h-4 text-red-500" />,
          text: 'text-red-400',
        };
      case 'MEDIUM':
        return {
          bg: alarm.acknowledged ? 'bg-yellow-500/10' : 'bg-yellow-500/20',
          border: 'border-l-yellow-500',
          icon: <AlertCircle className="w-4 h-4 text-yellow-500" />,
          text: 'text-yellow-400',
        };
      default:
        return {
          bg: alarm.acknowledged ? 'bg-blue-500/10' : 'bg-blue-500/20',
          border: 'border-l-blue-500',
          icon: <Info className="w-4 h-4 text-blue-500" />,
          text: 'text-blue-400',
        };
    }
  };

  const styles = getAlarmStyles();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={cn(
        'flex items-center gap-3 px-4 py-2 border-l-4',
        styles.bg,
        styles.border,
        !alarm.acknowledged && alarm.level === 'HIGH' && 'animate-pulse'
      )}
    >
      {styles.icon}
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn('text-xs font-mono font-bold', styles.text)}>
            {alarm.tag}
          </span>
          <span className="text-xs text-gray-500">
            {alarm.level}
          </span>
        </div>
        <p className="text-sm text-gray-300 truncate">
          {alarm.message}
        </p>
      </div>
      
      {!alarm.acknowledged && (
        <button
          onClick={onAcknowledge}
          className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
        >
          ACK
        </button>
      )}
      
      {alarm.acknowledged && (
        <Check className="w-4 h-4 text-green-500" />
      )}
    </motion.div>
  );
}


// Alarm Banner for top of screen
export function AlarmBanner() {
  const { state } = useProcessStore();
  const alarms = state?.alarms ?? [];
  const activeHighAlarms = alarms.filter((a) => a.level === 'HIGH' && !a.acknowledged);
  
  if (activeHighAlarms.length === 0) return null;

  return (
    <motion.div
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-red-500/90 text-white px-4 py-2 flex items-center justify-center gap-2"
    >
      <AlertTriangle className="w-5 h-5 animate-pulse" />
      <span className="font-bold">
        {activeHighAlarms.length} CRITICAL ALARM{activeHighAlarms.length > 1 ? 'S' : ''}
      </span>
      <span className="mx-2">|</span>
      <span className="text-sm">
        {activeHighAlarms[0]?.message}
      </span>
    </motion.div>
  );
}
