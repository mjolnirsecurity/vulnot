import { useEffect, useCallback, useRef } from 'react';
import { useProcessStore } from '@/stores/processStore';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const { setConnected, updateProcess, addAlarm } = useProcessStore();

  const connect = useCallback(() => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Connected to VULNOT');
        setConnected(true);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'process_update') updateProcess(data.data);
        if (data.type === 'alarm') addAlarm({ ...data.data, acknowledged: false });
      };
      
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      
      wsRef.current = ws;
    } catch (e) {
      console.log('WebSocket connection failed, using demo mode');
    }
  }, [setConnected, updateProcess, addAlarm]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const sendCommand = useCallback((command: string, params: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', command, params }));
    }
  }, []);

  return { sendCommand };
}
