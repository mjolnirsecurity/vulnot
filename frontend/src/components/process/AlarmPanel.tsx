'use client';

import { useProcessStore } from '@/stores/processStore';
import { Bell, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { cn, getAlarmColor } from '@/lib/utils';

export function AlarmPanel() {
  const { alarms, acknowledgeAlarm } = useProcessStore();
  const activeAlarms = alarms.filter(a => !a.acknowledged);
  
  const priorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return <XCircle className="w-4 h-4" />;
      case 'high': return <AlertTriangle className="w-4 h-4" />;
      default: return <Bell className="w-4 h-4" />;
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className={cn(
        'px-4 py-2 flex items-center justify-between',
        activeAlarms.length > 0 ? 'bg-red-600' : 'bg-gray-700'
      )}>
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5" />
          <span className="font-medium">Alarms</span>
        </div>
        <span className="bg-white/20 px-2 py-0.5 rounded text-sm">
          {activeAlarms.length} Active
        </span>
      </div>
      
      {/* Alarm List */}
      <div className="max-h-64 overflow-y-auto">
        {alarms.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            No alarms
          </div>
        ) : (
          alarms.map((alarm) => (
            <div
              key={alarm.id}
              className={cn(
                'px-4 py-2 border-b border-gray-700 flex items-center gap-3',
                alarm.acknowledged ? 'opacity-50' : ''
              )}
            >
              <div className={cn('p-1 rounded', getAlarmColor(alarm.priority))}>
                {priorityIcon(alarm.priority)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white truncate">
                  {alarm.tag.toUpperCase()} - {alarm.type.toUpperCase()}
                </div>
                <div className="text-xs text-gray-400">
                  Value: {alarm.value.toFixed(2)} | Limit: {alarm.limit}
                </div>
              </div>
              
              {!alarm.acknowledged && (
                <button
                  onClick={() => acknowledgeAlarm(alarm.id)}
                  className="p-1 hover:bg-gray-700 rounded"
                  title="Acknowledge"
                >
                  <CheckCircle className="w-4 h-4 text-green-400" />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
