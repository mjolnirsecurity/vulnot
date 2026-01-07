import { create } from 'zustand';

export interface Tank { level: number; inflow: number; outflow: number; }
export interface Pump { running: boolean; speed: number; flow: number; }
export interface Valve { position: number; }
export interface WaterQuality { ph: number; turbidity: number; chlorine: number; temperature: number; }
export interface Alarm { id: string; timestamp: string; tag: string; type: string; value: number; limit: number; priority: string; acknowledged: boolean; }
export interface TrendPoint { timestamp: number; value: number; }

interface ProcessState {
  connected: boolean;
  lastUpdate: string | null;
  tanks: Record<string, Tank>;
  pumps: Record<string, Pump>;
  valves: Record<string, Valve>;
  quality: WaterQuality;
  process: { flow_rate: number; pressure: number };
  alarms: Alarm[];
  trends: Record<string, TrendPoint[]>;
  setConnected: (connected: boolean) => void;
  updateProcess: (data: any) => void;
  addAlarm: (alarm: Alarm) => void;
  acknowledgeAlarm: (alarmId: string) => void;
  addTrendPoint: (tag: string, value: number) => void;
}

export const useProcessStore = create<ProcessState>((set, get) => ({
  connected: false,
  lastUpdate: null,
  tanks: {
    raw_water: { level: 75, inflow: 150, outflow: 145 },
    settling: { level: 60, inflow: 145, outflow: 140 },
    filter: { level: 45, inflow: 140, outflow: 135 },
    chlorine: { level: 80, inflow: 135, outflow: 130 },
    clear_well: { level: 90, inflow: 130, outflow: 200 },
    distribution: { level: 70, inflow: 200, outflow: 180 },
  },
  pumps: {
    intake: { running: true, speed: 75, flow: 150 },
    transfer1: { running: true, speed: 60, flow: 120 },
    transfer2: { running: false, speed: 0, flow: 0 },
    distribution: { running: true, speed: 80, flow: 200 },
    chemical: { running: true, speed: 25, flow: 5 },
  },
  valves: { inlet: { position: 100 }, outlet: { position: 75 }, bypass: { position: 0 }, drain: { position: 0 } },
  quality: { ph: 7.2, turbidity: 0.5, chlorine: 2.0, temperature: 18.5 },
  process: { flow_rate: 450, pressure: 65 },
  alarms: [
    { id: 'ALM-001', timestamp: new Date().toISOString(), tag: 'chlorine', type: 'high', value: 3.8, limit: 4.0, priority: 'high', acknowledged: false },
  ],
  trends: {},
  setConnected: (connected) => set({ connected }),
  updateProcess: (data) => set((state) => ({
    lastUpdate: data.timestamp || new Date().toISOString(),
    tanks: data.tanks || state.tanks,
    pumps: data.pumps || state.pumps,
    valves: data.valves || state.valves,
    quality: data.quality || state.quality,
    process: data.process || state.process,
  })),
  addAlarm: (alarm) => set((state) => ({ alarms: [alarm, ...state.alarms].slice(0, 50) })),
  acknowledgeAlarm: (alarmId) => set((state) => ({
    alarms: state.alarms.map((a) => a.id === alarmId ? { ...a, acknowledged: true } : a),
  })),
  addTrendPoint: (tag, value) => set((state) => {
    const now = Date.now();
    const currentTrend = state.trends[tag] || [];
    return { trends: { ...state.trends, [tag]: [...currentTrend.slice(-60), { timestamp: now, value }] } };
  }),
}));
