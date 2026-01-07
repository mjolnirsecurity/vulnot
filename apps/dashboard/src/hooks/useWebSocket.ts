'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useProcessStore } from '@/lib/store';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:9000';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { updateState, setConnected } = useProcessStore();

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    console.log('[WebSocket] Connecting to', `${WS_URL}/ws/process`);
    
    const ws = new WebSocket(`${WS_URL}/ws/process`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] Connected');
      setConnected(true);
      
      // Clear any pending reconnect
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle different message types
        if (data.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }));
          return;
        }
        
        if (data.type === 'pong') {
          return;
        }
        
        // Process state update
        if (data.timestamp) {
          updateState(data);
        }
      } catch (err) {
        console.error('[WebSocket] Parse error:', err);
      }
    };

    ws.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code, event.reason);
      setConnected(false);
      
      // Reconnect after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log('[WebSocket] Reconnecting...');
        connect();
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error);
    };
  }, [updateState, setConnected]);

  const sendCommand = useCallback((plcId: number, controlName: string, value: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        payload: {
          plc_id: plcId,
          control_name: controlName,
          value: value,
        },
      }));
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { sendCommand };
}
