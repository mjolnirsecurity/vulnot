'use client';

import { useProcessStore } from '@/stores/processStore';
import { Wifi, WifiOff } from 'lucide-react';

export function ConnectionStatus() {
  const connected = useProcessStore((state) => state.connected);
  const lastUpdate = useProcessStore((state) => state.lastUpdate);

  return (
    <div className="flex items-center gap-2">
      {connected ? (
        <>
          <Wifi className="w-4 h-4 text-green-500" />
          <span className="text-sm text-green-500">Connected</span>
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4 text-yellow-500 animate-pulse" />
          <span className="text-sm text-yellow-500">Demo Mode</span>
        </>
      )}
      {lastUpdate && (
        <span className="text-xs text-gray-500 ml-2">
          Last: {new Date(lastUpdate).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
